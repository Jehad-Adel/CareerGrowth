"""Schema for the Personalized Roadmap feature."""

from pydantic import BaseModel, Field


class RoadmapStep(BaseModel):
    """A single milestone in the candidate's career roadmap."""

    title: str = Field(description="Short title of this roadmap step.")
    description: str = Field(
        description="What the candidate should do in this step and why it matters."
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


class CareerRoadmap(BaseModel):
    """Structured, ordered roadmap toward a candidate's target role."""

    target_role: str = Field(description="The role the roadmap is built toward.")
    summary: str = Field(
        description="A concise 2-4 sentence overview of the roadmap and its rationale."
    )
    steps: list[RoadmapStep] = Field(
        description="Ordered list of roadmap steps, from first to last."
    )
    total_estimated_duration_months: float = Field(
        ge=0,
        description="Sum of all steps' estimated durations, in months.",
    )