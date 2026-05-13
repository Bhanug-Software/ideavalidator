from app.utils.config import client, MODEL, MAX_TOKENS
from app.utils.logger import logger

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


        prompt = f"""You are an expert project validator. Analyze this
        project idea and provide:
        1. A viability score (0-100)
        2. Your reasoning (why this score?)
        3. Your recommendation (build it or not?)

        Project idea: {project_idea}

        Answer the project idea with a natural langunage and dont use the ai buzzwords. Respond in this exact format:
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

        lines = response_text. strip().split("\n")

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
                recommendation = line.replace("RECOMMENDATION:", "").strip()
        
        return {
            "score": score,
            "reasoning" : reasoning,
            "recommendation" : recommendation,
            "raw_response" : response_text
            
        }




            