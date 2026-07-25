"""Schema for the Skill Gap Analyzer feature."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SkillGapItem(BaseModel):
    """A single missing or underdeveloped skill relative to the target job."""

    skill: str = Field(description="Name of the skill.")
    priority: Literal["Critical", "High", "Medium", "Low"] = Field(
        description=(
            "Critical: missing skill blocks hiring completely. High: important but the "
            "company could train for it. Medium: useful. Low: nice to have."
        )
    )
    importance_reason: str = Field(
        description="Why this skill matters for the target job, grounded in the job description."
    )
    current_level: Literal["None", "Beginner", "Intermediate", "Advanced"] = Field(
        description=(
            "None: not found in the CV. Beginner: mentioned once. Intermediate: used in a "
            "project. Advanced: backed by professional experience."
        )
    )
    estimated_learning_time: str = Field(
        description="Realistic time to close this gap, e.g. '2 weeks', '1 month', '3 months'."
    )
    prerequisite_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Other skills in this report that should be learned first, e.g. SQL before "
            "PostgreSQL optimization, Docker before Kubernetes. Empty list if none."
        ),
    )
    recommended_resources: list[str] = Field(
        min_length=2,
        max_length=4,
        description="2-4 resource names to learn this skill. Names only, never URLs.",
    )
    project_to_practice: str = Field(
        description="One realistic project idea to practice and demonstrate this skill."
    )
    mandatory: bool = Field(
        description="True if this skill is required to be considered for the target job."
    )


class SkillGapAnalysis(BaseModel):
    """Structured skill-gap report comparing a CV against a target job description."""

    overall_gap_score: int = Field(
        ge=0,
        le=100,
        description="Overall size of the skill gap, 0 (no gap) to 100 (completely unqualified).",
    )
    strongest_area: str = Field(description="The candidate's strongest area relative to the job.")
    weakest_area: str = Field(description="The candidate's weakest area relative to the job.")
    gap_summary: str = Field(
        description="A concise paragraph summarizing the overall skill gap and its impact."
    )
    missing_skills: list[SkillGapItem] = Field(
        description="Missing or underdeveloped skills, ordered by learning sequence and priority."
    )

    @model_validator(mode="after")
    def _dedupe_missing_skills(self) -> "SkillGapAnalysis":
        """Remove case-insensitive duplicate skill entries, keeping the first occurrence."""
        seen: set[str] = set()
        deduped: list[SkillGapItem] = []
        for item in self.missing_skills:
            key = item.skill.strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(item)
        self.missing_skills = deduped
        return self