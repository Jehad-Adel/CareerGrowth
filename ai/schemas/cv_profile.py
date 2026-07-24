from pydantic import BaseModel, Field
from typing import List, Optional


class CVProfile(BaseModel):
    """
    Structured output returned from the AI.
    """

    name: Optional[str] = None

    education: List[str] = Field(default_factory=list)

    skills: List[str] = Field(default_factory=list)

    projects: List[str] = Field(default_factory=list)

    experience: List[str] = Field(default_factory=list)

    certificates: List[str] = Field(default_factory=list)

    soft_skills: List[str] = Field(default_factory=list)

    strengths: List[str] = Field(default_factory=list)

    weaknesses: List[str] = Field(default_factory=list)

    missing_skills: List[str] = Field(default_factory=list)

    ats_score: int = 0

    summary: str = ""