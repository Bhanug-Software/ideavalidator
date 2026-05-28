# Output Validator - Pydantic Model for Claude's Response

from pydantic import BaseModel, Field, validator

class ProjectAnalysis(BaseModel):
    """Complete structured output from ValidatorAgent"""

    idea_summary: str = Field(description="Brief summary of the project idea")

    problem_statement: str = Field(description="The problem this idea solves")

    target_audience: str = Field(description="Who this product is for")

    market_validation: str = Field(description="Market size, demand, and validation from real data")

    competitor_analysis: str = Field(description="Real competitors and how this idea compares")

    mvp_recommendation: str = Field(description="What to build first as MVP")

    risk_analysis: str = Field(description="Key risks and how to mitigate them")

    final_recommendation: str = Field(description="Build it / Don't build it / Consider changes")

    @validator('final_recommendation')
    def validate_recommendation(cls, v):
        valid_options = ["Build it", "Don't build it", "Consider changes"]
        if v not in valid_options:
            raise ValueError(f"Recommendation must be one of: {valid_options}")
        return v
