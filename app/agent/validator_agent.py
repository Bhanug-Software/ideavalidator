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

        prompt = f"""You are an expert project validator with 20 years of experience evaluating startup ideas.

Analyze this project idea and provide a viability score (0-100), your reasoning, and a recommendation.
Use natural language. Don't use AI buzzwords or exaggerated language.

EXAMPLES OF GOOD OUTPUTS:
- Idea: Netflix clone
SCORE: 22
REASONING: Market saturated with Netflix, Disney+, Hulu, Amazon Prime. Content licensing costs billions per year. No competitive advantage without massive capital and exclusive content deals.
RECOMMENDATION: Don't build it

- Idea: AI email assistant for busy executives
SCORE: 68
REASONING: Growing market demand, clear ROI for enterprise. However, established competitors (Gmail, Outlook) have huge advantages. Needs unique differentiation.
RECOMMENDATION: Build it - with a specific niche angle

- Idea: Local flower delivery service
SCORE: 45
REASONING: Niche market with loyal customers but high logistics costs, limited scalability, and strong local competition. Difficult to expand beyond one city.
RECOMMENDATION: Consider changes - focus on subscription model or corporate contracts

- Idea: explain about RAG?
SCORE: 
REASONING: its not a project idea. Its a general AI topic about Retrieval Augment Generation
RECOMMENDATION: Consider sending only project ideas

Now analyze this project idea:
Project idea: {project_idea}

Respond in this exact format (ONLY the specified values, nothing extra):
SCORE: [number 0-100]
REASONING: [2-3 sentences]
RECOMMENDATION: [Build it / Don't build it / Consider changes]"""

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
        '''parse claude response into structred format'''

        lines = response_text.strip().split("\n")

        score = 0
        reasoning = ""
        recommendation = ""

        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score = int(line.replace("SCORE:", "").strip())
                except:
                    score = 0
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("RECOMMENDATION:"):
                rec_text = line.replace("RECOMMENDATION:", "").strip()
                # Extract only the base recommendation, ignoring extra details
                if "Build it" in rec_text:
                    recommendation = "Build it"
                elif "Don't build it" in rec_text:
                    recommendation = "Don't build it"
                elif "Consider changes" in rec_text:
                    recommendation = "Consider changes"
                else:
                    recommendation = rec_text

        # Validate parsed data using Pydantic model
        try:
            validated = ProjectAnalysis(
                score=score,
                reasoning=reasoning,
                recommendation=recommendation
            )
            logger.info("✅ Output validation passed - all fields are correct")
            return {
                "score": validated.score,
                "reasoning": validated.reasoning,
                "recommendation": validated.recommendation,
                "raw_response": response_text
            }
        except ValidationError as e:
            logger.error(f"❌ Output validation failed: {e}")
            return {
                "score": 0,
                "reasoning": f"Validation error: {str(e)}",
                "recommendation": "Please try again",
                "raw_response": response_text,
                "validation_failed": True
            }




            