import re
from concurrent.futures import ThreadPoolExecutor
from app.utils.config import client, MODEL, MAX_TOKENS
from app.utils.logger import logger
from app.utils.input_validator import input_validator
from app.utils.output_validator import ProjectAnalysis
from app.utils.cost_tracker import cost_tracker
from pydantic import ValidationError
from app.tools import custom_tools
from app.tools.tools_schema import TOOLS_SCHEMA
from langsmith import traceable

class ValidatorAgent:
    #AI Agent that validates the project ideas

    def __init__(self):
        #initialize the agent
        self.model = MODEL
        self.max_tokens = MAX_TOKENS
        self.tools = TOOLS_SCHEMA

    @traceable(name="execute_tool", tags=["tools", "execution"])
    def _execute_tool(self, tool_name, tool_input):
        """Execute a tool and return the result"""
        logger.info(f"🔧 Executing tool: {tool_name}")

        if tool_name == "send_email_to_user":
            return custom_tools.send_email_to_user(
                tool_input["email_address"],
                tool_input["subject"],
                tool_input["body"]
            )
        elif tool_name == "tavily_search":
            return custom_tools.tavily_search(
                tool_input["query"]
            )
        elif tool_name == "google_places_search":
            return custom_tools.google_places_search(
                tool_input["zipcode"],
                tool_input["business_type"]
            )
        else:
            return f"Unknown tool: {tool_name}"

    @traceable(name="validate_idea", tags=["validation", "claude"])
    def validate_idea(self, project_idea : str) -> dict:
        """validate a project idea
        
        args:
            project_idea: description of the project idea

        returns:
                dict with : score(0-100), reasoning, recommendation

        """
        logger.info(f"✓ Validation started for: {project_idea}")

        # STEP 1: Validate user input first
        is_valid, validation_message = input_validator.validate_complete(project_idea)

        if not is_valid:
            logger.error(f"❌ Input validation failed: {validation_message}")
            return {
                "score": 0,
                "reasoning": validation_message,
                "recommendation": "Please provide a valid project idea",
                "raw_response": validation_message,
                "validation_failed": True
            }

        logger.info("✅ Input validated successfully, sending to Claude...")

        prompt = f"""You are an expert startup advisor validating a project idea.

Here's the idea: {project_idea}

CRITICAL: Follow this exact sequence BEFORE writing your analysis:
1. FIRST: Check if user mentioned a zipcode or location. If yes, IMMEDIATELY use google_places_search with that zipcode and the business type.
2. THEN: Use tavily_search exactly 2 times:
   - First search: find real competitors for this idea
   - Second search: find current market size and demand for this idea
3. Only use send_email_to_user if the user explicitly asks to send results to their email.

IMPORTANT: When you find results from google_places_search, you MUST include them in your COMPETITOR_ANALYSIS section with their exact names, ratings, and Google Maps links.

Write in a casual, friendly tone - like advising a friend.
- Use regular dashes (-), NOT em dashes (—)
- Do NOT use markdown formatting (no **, no *, no ---, no ###)
- Plain text only

Format your response EXACTLY like this (keep every section, don't skip any):

IDEA_SUMMARY: [2-3 sentences describing what this idea is]

PROBLEM_STATEMENT: [What specific problem does this solve? Who feels this pain?]

TARGET_AUDIENCE: [Who exactly is this for? Age, role, situation - be specific]

MARKET_VALIDATION: [Real market size, demand signals, growth trends based on your search]

COMPETITOR_ANALYSIS: [List 3-5 real competitors found (including local ones from zipcode search), their ratings, and how this idea is different]

MVP_RECOMMENDATION: [What is the simplest version to build first? What features are must-haves vs nice-to-haves?]

RISK_ANALYSIS: [4-5 real risks with a short mitigation for each]

FINAL_RECOMMENDATION: [MUST be exactly one of: "Build it" OR "Don't build it" OR "Consider changes" - pick the one that best fits your analysis]"""

        # Send message to Claude with tools
        logger.info("→ Sending prompt to Claude API with tools...")
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Agentic loop - continue until Claude is done
        while True:
            # Check if this is the final call (no more tools needed)
            is_final_call = len(messages) > 1 and messages[-1].get("role") == "user"

            # Stream the final response, otherwise get full response for tool handling
            response_stream = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=TOOLS_SCHEMA,
                messages=messages,
                stream=is_final_call  # Stream only if we expect final text response
            )

            # Collect response content
            if is_final_call:
                # Stream mode - collect text as it arrives
                logger.info(f"→ Streaming analysis response...\n")
                response_text = ""
                total_input_tokens = 0
                total_output_tokens = 0

                for event in response_stream:
                    # Display text chunks in real-time
                    if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                        print(event.delta.text, end="", flush=True)
                        response_text += event.delta.text

                    # Collect token usage at the end
                    if event.type == "message_delta" and hasattr(event, "usage"):
                        total_input_tokens = event.usage.input_tokens
                        total_output_tokens = event.usage.output_tokens

                print()  # New line after streaming completes
                logger.info(f"\n← Streaming complete")

                # Track cost for streamed response
                call_cost = cost_tracker.add_usage(total_input_tokens, total_output_tokens)
                logger.info(f"💰 Cost for this call: {cost_tracker.format_cost(call_cost)}")

                message = None  # No message object in stream mode
                break

            else:
                # Non-streaming mode - get full response for tool processing
                message = response_stream
                logger.info(f"← Received response from Claude")

                # Track cost
                call_cost = cost_tracker.add_usage(
                    message.usage.input_tokens,
                    message.usage.output_tokens
                )
                logger.info(f"💰 Cost for this call: {cost_tracker.format_cost(call_cost)}")

                # Check if Claude called a tool
                tool_calls = [block for block in message.content if block.type == "tool_use"]

                if not tool_calls:
                    # No tool calls, Claude is done - extract the text response
                    break

            # Claude called tools - execute them
            logger.info(f"Claude requested {len(tool_calls)} tool call(s)")

            # Add Claude's response to messages
            messages.append({"role": "assistant", "content": message.content})

            # Execute each tool in parallel and collect results
            def run_tool(tool_call):
                logger.info(f"Executing: {tool_call.name}")
                try:
                    result = self._execute_tool(tool_call.name, tool_call.input)
                    logger.info(f"✅ Tool result received")
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    }
                except Exception as e:
                    logger.error(f"❌ Tool {tool_call.name} failed: {str(e)}")
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": f"Error executing {tool_call.name}: {str(e)}"
                    }

            tool_results = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(run_tool, tool_call) for tool_call in tool_calls]
                # Collect results with error handling
                for future in futures:
                    try:
                        result = future.result()
                        tool_results.append(result)
                    except Exception as e:
                        logger.error(f"❌ Unexpected error in tool execution: {str(e)}")
                        # Don't fail entire workflow if one tool has unexpected error
                        continue

            # Send tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        # Extract the final text response (if not already from streaming)
        if message is not None:
            response_text = next(
                (block.text for block in message.content if hasattr(block, "text")),
                ""
            )
        # else: response_text already collected from streaming above

        logger.info(f"← Final analysis received")

        # Parse the response
        result = self._parse_response(response_text)
        logger.info("✓ Analysis complete - check the response  below")

        return result
    
    #parsing the response text with the helper method

    def _clean_text(self, text: str) -> str:
        """Remove markdown and formatting artifacts from Claude's response"""
        text = text.replace("—", " - ")
        text = text.replace("–", "-")
        # Remove markdown bold/italic markers
        text = text.replace("**", "")
        text = text.replace("*", "")
        # Remove horizontal rules
        text = re.sub(r'\n---+\n', '\n', text)
        text = re.sub(r'\n===+\n', '\n', text)
        # Remove leading/trailing whitespace per line
        lines = [line.rstrip() for line in text.split('\n')]
        # Remove repeated blank lines
        cleaned = []
        prev_blank = False
        for line in lines:
            is_blank = line.strip() == ""
            if is_blank and prev_blank:
                continue
            cleaned.append(line)
            prev_blank = is_blank
        return '\n'.join(cleaned).strip()

    @traceable(name="parse_response", tags=["parsing", "claude"])
    def _parse_response(self, response_text: str) -> dict:
        '''parse claude response into structured format using regex'''

        def extract(label, next_label):
            pattern = rf'{label}:\s*(.+?)(?={next_label}:|$)'
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
            logger.warning(f"⚠️ {label} field not found in response")
            return ""

        idea_summary        = extract("IDEA_SUMMARY",        "PROBLEM_STATEMENT")
        problem_statement   = extract("PROBLEM_STATEMENT",   "TARGET_AUDIENCE")
        target_audience     = extract("TARGET_AUDIENCE",     "MARKET_VALIDATION")
        market_validation   = extract("MARKET_VALIDATION",   "COMPETITOR_ANALYSIS")
        competitor_analysis = extract("COMPETITOR_ANALYSIS", "MVP_RECOMMENDATION")
        mvp_recommendation  = extract("MVP_RECOMMENDATION",  "RISK_ANALYSIS")
        risk_analysis       = extract("RISK_ANALYSIS",       "FINAL_RECOMMENDATION")

        # Extract FINAL_RECOMMENDATION
        rec_match = re.search(r'FINAL_RECOMMENDATION:\s*(.+?)$', response_text, re.DOTALL)
        rec_text = rec_match.group(1).strip() if rec_match else ""

        # Smart recommendation mapping - handle variations
        rec_text_lower = rec_text.lower()
        if "don't build" in rec_text_lower or "do not build" in rec_text_lower:
            final_recommendation = "Don't build it"
        elif "consider changes" in rec_text_lower or "reconsider" in rec_text_lower:
            final_recommendation = "Consider changes"
        elif "build" in rec_text_lower:
            # Contains "build" - map to "Build it" (includes "cautiously build", "build it smart", etc.)
            final_recommendation = "Build it"
        else:
            # Default to "Consider changes" if we can't determine
            final_recommendation = "Consider changes"

        try:
            validated = ProjectAnalysis(
                idea_summary=idea_summary,
                problem_statement=problem_statement,
                target_audience=target_audience,
                market_validation=market_validation,
                competitor_analysis=competitor_analysis,
                mvp_recommendation=mvp_recommendation,
                risk_analysis=risk_analysis,
                final_recommendation=final_recommendation
            )
            logger.info("✅ Output validation passed - all fields are correct")
            return {
                "idea_summary":        self._clean_text(validated.idea_summary),
                "problem_statement":   self._clean_text(validated.problem_statement),
                "target_audience":     self._clean_text(validated.target_audience),
                "market_validation":   self._clean_text(validated.market_validation),
                "competitor_analysis": self._clean_text(validated.competitor_analysis),
                "mvp_recommendation":  self._clean_text(validated.mvp_recommendation),
                "risk_analysis":       self._clean_text(validated.risk_analysis),
                "final_recommendation": self._clean_text(validated.final_recommendation),
                "raw_response": response_text
            }
        except ValidationError as e:
            logger.error(f"❌ Output validation failed: {e}")
            return {
                "idea_summary": "",
                "problem_statement": "",
                "target_audience": "",
                "market_validation": "",
                "competitor_analysis": "",
                "mvp_recommendation": "",
                "risk_analysis": "",
                "final_recommendation": f"Validation error: {str(e)}",
                "raw_response": response_text,
                "validation_failed": True
            }

    def send_analysis_via_email(self, email_address: str, analysis_result: dict) -> str:
        """Send project analysis results via email

        args:
            email_address: User's email address
            analysis_result: Analysis results dictionary

        returns:
            Confirmation message
        """
        logger.info(f"📧 Preparing to send analysis to {email_address}")

        # Format the analysis into email body
        email_body = f"""PROJECT ANALYSIS RESULTS

IDEA SUMMARY:
{analysis_result['idea_summary']}

PROBLEM STATEMENT:
{analysis_result['problem_statement']}

TARGET AUDIENCE:
{analysis_result['target_audience']}

MARKET VALIDATION:
{analysis_result['market_validation']}

COMPETITOR ANALYSIS:
{analysis_result['competitor_analysis']}

MVP RECOMMENDATION:
{analysis_result['mvp_recommendation']}

RISK ANALYSIS:
{analysis_result['risk_analysis']}

FINAL RECOMMENDATION: {analysis_result['final_recommendation']}"""

        # Send email using the tool
        email_result = custom_tools.send_email_to_user(
            email_address=email_address,
            subject="Your Project Analysis Results",
            body=email_body
        )

        logger.info("✅ Email sent successfully")
        return email_result
