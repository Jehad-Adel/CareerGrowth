from typing import Literal

from pydantic import BaseModel, Field, model_validator

Difficulty = Literal["Beginner", "Intermediate", "Advanced"]

ResourceType = Literal["tutorial", "documentation", "course", "video", "book"]


class ResourceLink(BaseModel):
    title: str = Field(description="Title of the resource.")
    url: str | None = Field(
        default=None,
        description="URL to the resource. Only include if you are highly confident it is real.",
    )
    type: ResourceType = Field(description="Type of resource.")


class MicroPoint(BaseModel):
    title: str = Field(description="Short title of this micro-point.")
    description: str = Field(description="What to do in this micro-point.")


class RoadmapStep(BaseModel):
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
            "depends on. Empty list if this step has no prerequisites."
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
            "Realistic hours per week the candidate should put into this step."
        ),
    )
    micro_points: list[MicroPoint] = Field(
        default_factory=list,
        description=(
            "3-7 granular, actionable sub-steps that break this step down into "
            "concrete micro-actions. Each micro-point has a title and description."
        ),
    )
    learning_resources: list[ResourceLink] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "Curated learning resources (tutorials, documentation, courses, videos, books) "
            "with title, optional URL, and type. Include real resources you are confident exist."
        ),
    )
    recommended_resources: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Legacy resource or platform names only. Prefer learning_resources instead.",
    )
    project_to_practice: str = Field(
        default="",
        description="One realistic, scoped project idea that demonstrates this step's skills.",
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
        self.total_estimated_duration_months = round(
            sum(step.estimated_duration_months for step in self.steps), 1
        )
        return self
