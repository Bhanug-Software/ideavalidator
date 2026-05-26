# Output Validator - Pydantic Model for Claude's Response
# Comprehensive project analysis model for any domain

from pydantic import BaseModel, Field, validator
from loguru import logger

class ProjectAnalysis(BaseModel):
    """Complete structured output from ValidatorAgent"""

    score: int = Field(
        ge=0,
        le=100,
        description="Viability score from 0-100"
    )

    recommendation: str = Field(
        description="Build it / Don't build it / Consider changes"
    )

    market_opportunity: str = Field(
        description="Market size, demand, and competition analysis"
    )

    feasibility: str = Field(
        description="Technical complexity, required skills, timeline, budget"
    )

    resources_required: str = Field(
        description="Team composition, skills, capital, and timeline needed"
    )

    dos: str = Field(
        description="Critical DO's during development (what to focus on)"
    )

    donts: str = Field(
        description="Critical DON'Ts during development (what to avoid)"
    )

    key_risks: str = Field(
        description="Key risks and mitigation strategies"
    )

    timeline: str = Field(
        description="Realistic timeline and phases"
    )

    next_step: str = Field(
        description="Immediate next action to take"
    )

    changes_required: str = Field(
        description="If recommendation is 'Consider changes': what specific changes to make",
        default=""
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
