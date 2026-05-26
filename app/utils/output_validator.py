# Output Validator - Pydantic Model for Claude's Response
# This file will contain the ProjectAnalysis Pydantic model
# to validate Claude's output structure

from pydantic import BaseModel, Field, validator
from loguru import logger

class ProjectAnalysis(BaseModel):
    """Structured output from ValidatorAgent - with validation rules"""

    score: int = Field(
        ge=0,
        le=100,
        description="Viability score from 0-100"
    )

    reasoning: str = Field(
        min_length=20,
        description="Why this score? (2-3 sentences)"
    )

    recommendation: str = Field(
        description="Build it / Don't build it / Consider changes"
    )

    @validator('recommendation')
    def validate_recommendation(cls, v):
        """Check that recommendation is one of 3 valid options"""
        valid_options = [
            "Build it",
            "Don't build it",
            "Consider changes"
        ]

        if v not in valid_options:
            raise ValueError(f"Recommendation must be one of: {valid_options}")

        return v
