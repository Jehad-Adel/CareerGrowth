"""Schema for the Personalized Roadmap feature."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Difficulty = Literal["Beginner", "Intermediate", "Advanced"]


class RoadmapStep(BaseModel):
    """A single milestone in the candidate's career roadmap."""

    title: str = Field(description="Short title of this roadmap step.")
    description: str = Field(description="What the candidate should do in this step.")
    reason: str = Field(
        default="",
        description=(
            "Why this step exists and why it comes at this point in the sequence "
            "for this specific candidate, referencing their actual profile and the "
            "target role."
        ),
    )
    difficulty: Difficulty = Field(
        default="Intermediate",
        description="Difficulty of this step relative to the candidate's current level.",
    )
    skills_to_acquire: list[str] = Field(
        description="Specific skills to acquire or strengthen during this step. Empty list if none."
    )
    prerequisite_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills from earlier steps (or already held by the candidate) that this step "
            "depends on, e.g. Docker before Kubernetes, SQL before PostgreSQL optimization, "
            "Git before CI/CD. Empty list if this step has no prerequisites."
        ),
    )
    estimated_duration_months: float = Field(
        gt=0,
        description="Estimated time in months to complete this step.",
    )
    estimated_weekly_hours: float = Field(
        default=0,
        ge=0,
        description=(
            "Realistic hours per week the candidate should put into this step. The "
            "duration alone does not say whether a step is an evening habit or a "
            "second job."
        ),
    )
    recommended_resources: list[str] = Field(
        default_factory=list,
        max_length=4,
        description=(
            "Two to four resource or platform names for this step. Names only, "
            "never URLs — a hallucinated link is worse than no link."
        ),
    )
    project_to_practice: str = Field(
        default="",
        description=(
            "One realistic, scoped project idea that demonstrates this step's skills."
        ),
    )


class CareerRoadmap(BaseModel):
    """Structured, ordered roadmap toward a candidate's target role."""

    target_role: str = Field(description="The role the roadmap is built toward.")
    summary: str = Field(
        description=(
            "A concise 2-4 sentence overview of the roadmap, referencing specific "
            "aspects of this candidate's profile rather than generic advice."
        )
    )
    steps: list[RoadmapStep] = Field(
        description="Ordered list of roadmap steps, from first to last."
    )
    total_estimated_duration_months: float = Field(
        ge=0,
        description="Sum of all steps' estimated durations, in months.",
    )

    @model_validator(mode="after")
    def _recompute_total_duration(self) -> "CareerRoadmap":
        """Re-add the steps rather than trusting the model's own sum.

        The total drives the roadmap header and the farm's horizon, and a
        figure that disagrees with the steps under it reads as a bug to the
        user whichever number is right.
        """
        self.total_estimated_duration_months = round(
            sum(step.estimated_duration_months for step in self.steps), 1
        )
        return self
