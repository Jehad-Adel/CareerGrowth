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
    skills_to_acquire: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
    prerequisite_skills: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
    estimated_months: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    # todo | done
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="todo", server_default="todo"
    )

    roadmap: Mapped["Roadmap"] = relationship(back_populates="steps")
