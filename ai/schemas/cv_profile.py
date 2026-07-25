"""Schema for the CV Analysis feature."""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SeniorityLevel(str, Enum):
    """Career seniority tiers used across CV Analysis and Job Matching."""

    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"


class CVProfile(BaseModel):
    """Structured representation of a candidate extracted from their CV.

    Field descriptions double as the extraction instructions passed to
    the LLM through `with_structured_output`, so they must be precise.
    """

    full_name: str | None = Field(
        default=None,
        description="Candidate's full name as it appears on the CV, if present.",
    )
    current_role: str | None = Field(
        default=None,
        description="The candidate's most recent or current job title.",
    )
    years_of_experience: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Total professional experience in years, computed only from explicitly stated "
            "employment dates. Null if the CV does not provide enough explicit dates to "
            "compute this without guessing."
        ),
    )
    seniority_level: SeniorityLevel = Field(
        description=(
            "Overall seniority based only on explicitly stated job titles and the computed "
            "years_of_experience. Never guessed from unstated context."
        )
    )
    skills: list[str] = Field(
        description="Technical and professional skills explicitly demonstrated in the CV."
    )
    strengths: list[str] = Field(
        description="Notable strengths of the candidate based on their experience and achievements."
    )
    weaknesses: list[str] = Field(
        description="Gaps, inconsistencies, or areas that weaken the CV's overall impact."
    )
    summary: str = Field(
        description="A concise 2-4 sentence professional summary of the candidate."
    )
    improvement_suggestions: list[str] = Field(
        description="Concrete, actionable suggestions to improve the CV's content or presentation."
    )

    @model_validator(mode="after")
    def _dedupe_skills(self) -> "CVProfile":
        """Remove case-insensitive duplicate skills, preserving first occurrence and order."""
        seen: set[str] = set()
        deduped: list[str] = []
        for skill in self.skills:
            key = skill.strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(skill.strip())
        self.skills = deduped
        return self