import re
from typing import TypedDict, Any
from concurrent.futures import ThreadPoolExecutor
from langgraph.graph import StateGraph, END
from app.utils.config import client, MODEL, MAX_TOKENS
from app.utils.logger import logger
from app.utils.input_validator import input_validator
from app.utils.output_validator import ProjectAnalysis
from pydantic import ValidationError
from app.tools import custom_tools
from app.tools.tools_schema import TOOLS_SCHEMA
from langsmith import traceable


# Define the workflow state
class AnalysisState(TypedDict):
    """State that flows through the LangGraph workflow"""
    project_idea: str
    messages: list
    response: Any
    response_text: str
    validation_error: bool
    error_message: str
    final_result: dict


class ValidatorAgent:
    """AI Agent that validates project ideas using LangGraph workflow"""

    def __init__(self):
        """Initialize the agent with model config and build workflow"""
        self.model = MODEL
        self.max_tokens = MAX_TOKENS
        self.tools = TOOLS_SCHEMA
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow"""
        from langgraph.graph import START
        graph = StateGraph(AnalysisState)

        # Add workflow nodes (steps)
        graph.add_node("validate_input", self._node_validate_input)
        graph.add_node("call_claude", self._node_call_claude)
        graph.add_node("execute_tools", self._node_execute_tools)
        graph.add_node("parse_response", self._node_parse_response)

        # Add edges (connections)
        graph.add_edge(START, "validate_input")
        graph.add_edge("validate_input", "call_claude")
        graph.add_conditional_edges(
            "call_claude",
            self._should_execute_tools,
            {
                "execute": "execute_tools",
                "parse": "parse_response"
            }
        )
        graph.add_edge("execute_tools", "call_claude")
        graph.add_edge("parse_response", END)

        return graph.compile()

    @traceable(name="validate_input_node", tags=["validation", "node"])
    def _node_validate_input(self, state: AnalysisState) -> AnalysisState:
        """Node 1: Validate user input"""
        logger.info(f"✓ Validation started for: {state['project_idea']}")

        is_valid, validation_message = input_validator.validate_complete(state["project_idea"])

        if not is_valid:
            logger.error(f"❌ Input validation failed: {validation_message}")
            return {
                **state,
                "validation_error": True,
                "error_message": validation_message,
                "final_result": {
                    "score": 0,
                    "reasoning": validation_message,
                    "recommendation": "Please provide a valid project idea",
                    "raw_response": validation_message,
                    "validation_failed": True
                }
            }

        logger.info("✅ Input validated successfully, sending to Claude...")

        prompt = f"""You are an expert startup advisor validating a project idea.

Here's the idea: {state['project_idea']}

CRITICAL: Follow this exact sequence BEFORE writing your analysis:
1. FIRST: Check if user mentioned a zipcode or location. If yes, IMMEDIATELY use google_places_search with that zipcode and the business type.
2. THEN: Use tavily_search exactly 3 times:
   - First search: find real competitors for this idea
   - Second search: find current market size and demand for this idea
   - Third Search: find the similar business not the competitors.
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

        logger.info("→ Sending prompt to Claude API with tools...")
        messages = [{"role": "user", "content": prompt}]

        return {**state, "messages": messages, "validation_error": False}

    @traceable(name="call_claude_node", tags=["claude", "node"])
    def _node_call_claude(self, state: AnalysisState) -> AnalysisState:
        """Node 2: Call Claude API"""
        logger.info(f"← Calling Claude API")

        # Check if this is the final call (no more tools needed)
        is_final_call = len(state["messages"]) > 1 and state["messages"][-1].get("role") == "user"

        response_stream = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            tools=TOOLS_SCHEMA,
            messages=state["messages"],
            stream=is_final_call
        )

        if is_final_call:
            # Stream mode - collect text as it arrives
            logger.info(f"→ Streaming analysis response...\n")
            response_text = ""

            for event in response_stream:
                if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                    print(event.delta.text, end="", flush=True)
                    response_text += event.delta.text

            print()  # New line after streaming
            logger.info(f"\n← Streaming complete")
            return {**state, "response": None, "response_text": response_text}
        else:
            # Non-streaming mode
            logger.info(f"← Received response from Claude")
            return {**state, "response": response_stream}

    def _should_execute_tools(self, state: AnalysisState) -> str:
        """Conditional logic: Should we execute tools or parse response?"""
        if state["response"] is None:
            # Streaming mode - response already collected, go to parse
            return "parse"

        # Non-streaming mode - check for tool calls
        tool_calls = [block for block in state["response"].content if block.type == "tool_use"]

        if not tool_calls:
            # No tools called, extract text and parse
            response_text = next(
                (block.text for block in state["response"].content if hasattr(block, "text")),
                ""
            )
            state["response_text"] = response_text
            return "parse"

        return "execute"

    @traceable(name="execute_tools_node", tags=["tools", "node"])
    def _node_execute_tools(self, state: AnalysisState) -> AnalysisState:
        """Node 3: Execute tools called by Claude"""
        tool_calls = [block for block in state["response"].content if block.type == "tool_use"]
        logger.info(f"Claude requested {len(tool_calls)} tool call(s)")

        # Add Claude's response to messages
        messages = state["messages"] + [{"role": "assistant", "content": state["response"].content}]

        # Execute tools
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
            for future in futures:
                try:
                    result = future.result()
                    tool_results.append(result)
                except Exception as e:
                    logger.error(f"❌ Unexpected error in tool execution: {str(e)}")
                    continue

        # Send tool results back to Claude
        messages.append({"role": "user", "content": tool_results})

        return {**state, "messages": messages, "response": None}

    @traceable(name="parse_response_node", tags=["parsing", "node"])
    def _node_parse_response(self, state: AnalysisState) -> AnalysisState:
        """Node 4: Parse and validate Claude's response"""
        logger.info(f"← Final analysis received")

        result = self._parse_response(state["response_text"])
        logger.info("✓ Analysis complete")

        return {**state, "final_result": result}

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
            return custom_tools.tavily_search(tool_input["query"])
        elif tool_name == "google_places_search":
            return custom_tools.google_places_search(
                tool_input["zipcode"],
                tool_input["business_type"]
            )
        else:
            return f"Unknown tool: {tool_name}"

    def _clean_text(self, text: str) -> str:
        """Remove markdown and formatting artifacts from Claude's response"""
        text = text.replace("—", " - ")
        text = text.replace("–", "-")
        text = text.replace("**", "")
        text = text.replace("*", "")
        text = re.sub(r'\n---+\n', '\n', text)
        text = re.sub(r'\n===+\n', '\n', text)
        lines = [line.rstrip() for line in text.split('\n')]
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
        """Parse claude response into structured format using regex"""

        def extract(label, next_label):
            pattern = rf'{label}:\s*(.+?)(?={next_label}:|$)'
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
            logger.warning(f"⚠️ {label} field not found in response")
            return ""

        idea_summary = extract("IDEA_SUMMARY", "PROBLEM_STATEMENT")
        problem_statement = extract("PROBLEM_STATEMENT", "TARGET_AUDIENCE")
        target_audience = extract("TARGET_AUDIENCE", "MARKET_VALIDATION")
        market_validation = extract("MARKET_VALIDATION", "COMPETITOR_ANALYSIS")
        competitor_analysis = extract("COMPETITOR_ANALYSIS", "MVP_RECOMMENDATION")
        mvp_recommendation = extract("MVP_RECOMMENDATION", "RISK_ANALYSIS")
        risk_analysis = extract("RISK_ANALYSIS", "FINAL_RECOMMENDATION")

        rec_match = re.search(r'FINAL_RECOMMENDATION:\s*(.+?)$', response_text, re.DOTALL)
        rec_text = rec_match.group(1).strip() if rec_match else ""

        rec_text_lower = rec_text.lower()
        if "don't build" in rec_text_lower or "do not build" in rec_text_lower:
            final_recommendation = "Don't build it"
        elif "consider changes" in rec_text_lower or "reconsider" in rec_text_lower:
            final_recommendation = "Consider changes"
        elif "build" in rec_text_lower:
            final_recommendation = "Build it"
        else:
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
            logger.info("✅ Output validation passed")
            return {
                "idea_summary": self._clean_text(validated.idea_summary),
                "problem_statement": self._clean_text(validated.problem_statement),
                "target_audience": self._clean_text(validated.target_audience),
                "market_validation": self._clean_text(validated.market_validation),
                "competitor_analysis": self._clean_text(validated.competitor_analysis),
                "mvp_recommendation": self._clean_text(validated.mvp_recommendation),
                "risk_analysis": self._clean_text(validated.risk_analysis),
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

    def validate_idea(self, project_idea: str) -> dict:
        """Validate a project idea using LangGraph workflow

        Args:
            project_idea: Description of the project idea

        Returns:
            dict with analysis results
        """
        logger.info(f"✓ Validation started for: {project_idea}")

        # Initialize state and run workflow
        initial_state = {
            "project_idea": project_idea,
            "messages": [],
            "response": None,
            "response_text": "",
            "validation_error": False,
            "error_message": "",
            "final_result": {}
        }

        result = self.workflow.invoke(initial_state)

        if result["validation_error"]:
            return result["final_result"]

        return result["final_result"]

    def send_analysis_via_email(self, email_address: str, analysis_result: dict) -> str:
        """Send project analysis results via email

        Args:
            email_address: User's email address
            analysis_result: Analysis results dictionary

        Returns:
            Confirmation message
        """
        logger.info(f"📧 Preparing to send analysis to {email_address}")

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

        email_result = custom_tools.send_email_to_user(
            email_address=email_address,
            subject="Your Project Analysis Results",
            body=email_body
        )

        logger.info("✅ Email sent successfully")
        return email_result
