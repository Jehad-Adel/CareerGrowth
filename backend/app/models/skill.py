import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Skill(UUIDPrimaryKey, Timestamps, Base):
    """A plant on the farm. Mastery drives how grown it renders."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_skill_name"),)

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(60))
    mastery: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # cv | job_match | skill_gap | roadmap | manual
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    profile: Mapped["CareerProfile"] = relationship(back_populates="skills")
