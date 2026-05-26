import re
from app.utils.config import client, MODEL, MAX_TOKENS
from app.utils.logger import logger
from app.utils.input_validator import input_validator
from app.utils.output_validator import ProjectAnalysis
from pydantic import ValidationError

class ValidatorAgent:
    #AI Agent that validates the project ideas

    def __init__(self):
        #initialize the agent
        self.model =MODEL
        self.max_tokens = MAX_TOKENS

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

        prompt = f"""You are someone who helps people decide if their project ideas are good.

I will give you a project idea. Please analyze it and give honest feedback.
Use simple words. No technical jargon. Speak like a friend helping a friend.

Project idea: {project_idea}

Please respond in this format (ONLY the values, nothing extra):

SCORE: [number between 0 and 100]

RECOMMENDATION: [Build it / Don't build it / Consider changes]

MARKET_OPPORTUNITY: [Simple explanation: Is there real demand? Who needs it? How many people?]

FEASIBILITY: [Simple explanation: Is it hard to build? How long will it take? How much money needed?]

RESOURCES_REQUIRED: [Simple explanation: What kind of people do you need? How much will it cost?]

DOS: [5-6 things that are important to do, format as bullet points with • prefix]

DONTS: [5-6 things to avoid doing, format as bullet points with • prefix]

KEY_RISKS: [4-5 problems that could happen and how to fix them, format as "Problem: Solution"]

TIMELINE: [How long will it take? Break it into simple phases with time]

NEXT_STEP: [One thing to do this week to check if your idea is good]

CHANGES_REQUIRED: [If recommendation is 'Consider changes': what to change to make it better. If other: write 'N/A']"""

        # Send message to Claude
        logger.info("→ Sending prompt to Claude API...")
        message = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract Claude's response
        response_text = message.content[0].text
        logger.info(f"← Received response from Claude")

        # Parse the response
        result = self._parse_response(response_text)
        logger.info("✓ Analysis complete - check the response  below")

        return result
    
    #parsing the response text with the helper method

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
            changes_required = changes_match.group(1).strip()
        else:
            logger.warning("⚠️ CHANGES_REQUIRED field not found in response")

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
                "recommendation": validated.recommendation,
                "market_opportunity": validated.market_opportunity,
                "feasibility": validated.feasibility,
                "resources_required": validated.resources_required,
                "dos": validated.dos,
                "donts": validated.donts,
                "key_risks": validated.key_risks,
                "timeline": validated.timeline,
                "next_step": validated.next_step,
                "changes_required": validated.changes_required,
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




            