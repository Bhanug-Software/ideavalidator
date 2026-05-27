import re
import json
import os
from app.utils.config import client, MODEL, MAX_TOKENS
from app.utils.logger import logger
from app.utils.input_validator import input_validator
from app.utils.output_validator import ProjectAnalysis
from app.utils.cost_tracker import cost_tracker
from pydantic import ValidationError
from app.tools import custom_tools
from app.tools.tools_schema import TOOLS_SCHEMA
from langsmith import traceable

os.environ.setdefault("LANGSMITH_TRACING", "true")

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

        prompt = f"""You're a mentor helping someone figure out if their project idea is worth building.

Here's their idea: {project_idea}

Give them honest, friendly feedback. Write like you're texting a friend - casual, natural, real.
- No corporate speak
- No fancy terminology
- Keep it short and punchy
- Be encouraging but honest
- IMPORTANT: Use regular dashes (-) or commas, NOT em dashes (—)

You have access to tools for supply chain data. Use them if the idea involves suppliers, logistics, compliance, or market research.

Format your response EXACTLY like this (keep each section, don't skip):

SCORE: [0-100 number]

RECOMMENDATION: [Build it / Don't build it / Consider changes]

MARKET_OPPORTUNITY: [Casual explanation - real demand? Who wants it? How many people?]

FEASIBILITY: [Is it doable? How long? Cost estimate? Be real about it.]

RESOURCES_REQUIRED: [What team do you need? Budget reality?]

DOS: [5-6 bullet points with • - things to actually do]

DONTS: [5-6 bullet points with • - real traps to avoid]

KEY_RISKS: [4-5 actual problems that could happen, with quick fixes]

TIMELINE: [Break down the months - be realistic]

NEXT_STEP: [One concrete thing they should do this week]

CHANGES_REQUIRED: [If you said 'Consider changes' above, list 3-5 specific tweaks. Otherwise write 'N/A']"""

        # Send message to Claude with tools
        logger.info("→ Sending prompt to Claude API with tools...")
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Agentic loop - continue until Claude is done
        while True:
            message = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=TOOLS_SCHEMA,
                messages=messages
            )

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

            # Execute each tool and collect results
            tool_results = []
            for tool_call in tool_calls:
                logger.info(f"Executing: {tool_call.name}")
                tool_result = self._execute_tool(tool_call.name, tool_call.input)
                logger.info(f"✅ Tool result received")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": tool_result
                })

            # Send tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        # Extract the final text response
        response_text = next(
            (block.text for block in message.content if hasattr(block, "text")),
            ""
        )
        logger.info(f"← Received final analysis from Claude")

        # Parse the response
        result = self._parse_response(response_text)
        logger.info("✓ Analysis complete - check the response  below")

        return result
    
    #parsing the response text with the helper method

    def _clean_text(self, text: str) -> str:
        """Remove em dashes and other formatting issues"""
        # Replace em dashes with regular dashes or commas
        text = text.replace("—", " - ")
        text = text.replace("–", "-")
        return text

    @traceable(name="parse_response", tags=["parsing", "claude"])
    def _parse_response(self, response_text : str) -> dict :
        '''parse claude response into structured format using regex for robustness'''

        score = 0
        recommendation = ""
        market_opportunity = ""
        feasibility = ""
        resources_required = ""
        dos = ""
        donts = ""
        key_risks = ""
        timeline = ""
        next_step = ""
        changes_required = ""

        # Extract SCORE
        score_match = re.search(r'SCORE:\s*(\d+)', response_text)
        if score_match:
            try:
                score = int(score_match.group(1))
            except ValueError:
                logger.warning("⚠️ Could not parse score, defaulting to 0")
                score = 0
        else:
            logger.warning("⚠️ SCORE field not found in response")

        # Extract RECOMMENDATION
        rec_match = re.search(r'RECOMMENDATION:\s*(.+?)(?=MARKET_OPPORTUNITY:|$)', response_text, re.DOTALL)
        if rec_match:
            rec_text = rec_match.group(1).strip()
            if "Build it" in rec_text:
                recommendation = "Build it"
            elif "Don't build it" in rec_text:
                recommendation = "Don't build it"
            elif "Consider changes" in rec_text:
                recommendation = "Consider changes"
            else:
                recommendation = rec_text
        else:
            logger.warning("⚠️ RECOMMENDATION field not found in response")

        # Extract MARKET_OPPORTUNITY
        market_match = re.search(r'MARKET_OPPORTUNITY:\s*(.+?)(?=FEASIBILITY:|$)', response_text, re.DOTALL)
        if market_match:
            market_opportunity = market_match.group(1).strip()
        else:
            logger.warning("⚠️ MARKET_OPPORTUNITY field not found in response")

        # Extract FEASIBILITY
        feasibility_match = re.search(r'FEASIBILITY:\s*(.+?)(?=RESOURCES_REQUIRED:|$)', response_text, re.DOTALL)
        if feasibility_match:
            feasibility = feasibility_match.group(1).strip()
        else:
            logger.warning("⚠️ FEASIBILITY field not found in response")

        # Extract RESOURCES_REQUIRED
        resources_match = re.search(r'RESOURCES_REQUIRED:\s*(.+?)(?=DOS:|$)', response_text, re.DOTALL)
        if resources_match:
            resources_required = resources_match.group(1).strip()
        else:
            logger.warning("⚠️ RESOURCES_REQUIRED field not found in response")

        # Extract DOS
        dos_match = re.search(r'DOS:\s*(.+?)(?=DONTS:|$)', response_text, re.DOTALL)
        if dos_match:
            dos = dos_match.group(1).strip()
        else:
            logger.warning("⚠️ DOS field not found in response")

        # Extract DONTS
        donts_match = re.search(r'DONTS:\s*(.+?)(?=KEY_RISKS:|$)', response_text, re.DOTALL)
        if donts_match:
            donts = donts_match.group(1).strip()
        else:
            logger.warning("⚠️ DONTS field not found in response")

        # Extract KEY_RISKS
        risks_match = re.search(r'KEY_RISKS:\s*(.+?)(?=TIMELINE:|$)', response_text, re.DOTALL)
        if risks_match:
            key_risks = risks_match.group(1).strip()
        else:
            logger.warning("⚠️ KEY_RISKS field not found in response")

        # Extract TIMELINE
        timeline_match = re.search(r'TIMELINE:\s*(.+?)(?=NEXT_STEP:|$)', response_text, re.DOTALL)
        if timeline_match:
            timeline = timeline_match.group(1).strip()
        else:
            logger.warning("⚠️ TIMELINE field not found in response")

        # Extract NEXT_STEP
        next_step_match = re.search(r'NEXT_STEP:\s*(.+?)(?=CHANGES_REQUIRED:|$)', response_text, re.DOTALL)
        if next_step_match:
            next_step = next_step_match.group(1).strip()
        else:
            logger.warning("⚠️ NEXT_STEP field not found in response")

        # Extract CHANGES_REQUIRED
        changes_match = re.search(r'CHANGES_REQUIRED:\s*(.+?)$', response_text, re.MULTILINE | re.DOTALL)
        if changes_match:
            changes_text = changes_match.group(1).strip()
            if changes_text and changes_text.lower() != "n/a":
                changes_required = changes_text
            else:
                changes_required = "N/A"
        else:
            logger.warning("⚠️ CHANGES_REQUIRED field not found in response")
            changes_required = "N/A"

        # Validate parsed data using Pydantic model
        try:
            validated = ProjectAnalysis(
                score=score,
                recommendation=recommendation,
                market_opportunity=market_opportunity,
                feasibility=feasibility,
                resources_required=resources_required,
                dos=dos,
                donts=donts,
                key_risks=key_risks,
                timeline=timeline,
                next_step=next_step,
                changes_required=changes_required
            )
            logger.info("✅ Output validation passed - all fields are correct")
            return {
                "score": validated.score,
                "recommendation": self._clean_text(validated.recommendation),
                "market_opportunity": self._clean_text(validated.market_opportunity),
                "feasibility": self._clean_text(validated.feasibility),
                "resources_required": self._clean_text(validated.resources_required),
                "dos": self._clean_text(validated.dos),
                "donts": self._clean_text(validated.donts),
                "key_risks": self._clean_text(validated.key_risks),
                "timeline": self._clean_text(validated.timeline),
                "next_step": self._clean_text(validated.next_step),
                "changes_required": self._clean_text(validated.changes_required),
                "raw_response": response_text
            }
        except ValidationError as e:
            logger.error(f"❌ Output validation failed: {e}")
            return {
                "score": 0,
                "recommendation": "Please try again",
                "market_opportunity": "",
                "feasibility": "",
                "resources_required": "",
                "dos": "",
                "donts": "",
                "key_risks": "",
                "timeline": "",
                "next_step": f"Validation error: {str(e)}",
                "changes_required": "",
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

Score: {analysis_result['score']} out of 100

RECOMMENDATION: {analysis_result['recommendation']}

MARKET OPPORTUNITY:
{analysis_result['market_opportunity']}

FEASIBILITY:
{analysis_result['feasibility']}

RESOURCES REQUIRED:
{analysis_result['resources_required']}

DO's:
{analysis_result['dos']}

DON'Ts:
{analysis_result['donts']}

KEY RISKS:
{analysis_result['key_risks']}

TIMELINE:
{analysis_result['timeline']}

NEXT STEP:
{analysis_result['next_step']}

CHANGES REQUIRED:
{analysis_result['changes_required']}"""

        # Send email using the tool
        email_result = custom_tools.send_email_to_user(
            email_address=email_address,
            subject="Your Project Analysis Results",
            body=email_body
        )

        logger.info("✅ Email sent successfully")
        return email_result
