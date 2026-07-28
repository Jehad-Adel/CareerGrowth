import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class Roadmap(UUIDPrimaryKey, Timestamps, Base):
    """An ordered path from the current profile toward a target role."""

    __tablename__ = "roadmaps"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    total_estimated_months: Mapped[float] = mapped_column(
        Numeric(5, 1), nullable=False
    )
    # The chain's raw output, kept so a bad generation stays diagnosable.
    result: Mapped[dict] = mapped_column(JSONType, nullable=False)

    steps: Mapped[list["RoadmapStep"]] = relationship(
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapStep.position",
        lazy="selectin",
    )


class RoadmapStep(UUIDPrimaryKey, Timestamps, Base):
    """One milestone. Completing it is what makes the farm grow."""

    __tablename__ = "roadmap_steps"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalised from the parent so a step can be authorized without a join.
    # Every service method filters on profile_id; this keeps that cheap.
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Why this step, and why here in the order, for this person specifically.
    # Separate from `description` so the UI can show the plan and the argument
    # for the plan independently.
    reason: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    # Beginner | Intermediate | Advanced, relative to the candidate's level.
    difficulty: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Intermediate", server_default="Intermediate"
    )
    skills_to_acquire: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
    prerequisite_skills: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
    # Resource and platform *names*, never URLs — a hallucinated link is worse
    # than no link, and there is no way to validate one at generation time.
    recommended_resources: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
    project_to_practice: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    estimated_months: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    # Duration alone cannot say whether a step is an evening habit or a second
    # job. Zero means the generation did not estimate it.
    estimated_weekly_hours: Mapped[float] = mapped_column(
        Numeric(4, 1), nullable=False, default=0, server_default="0"
    )
    # todo | done
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="todo", server_default="todo"
    )

    roadmap: Mapped["Roadmap"] = relationship(back_populates="steps")
