import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Skill(UUIDPrimaryKey, Timestamps, Base):
    """A plant on the farm. Mastery drives how grown it renders."""

    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(60))
    mastery: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # cv | job_match | skill_gap | roadmap | manual
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    profile: Mapped["CareerProfile"] = relationship(back_populates="skills")

    @declared_attr.directive
    def __table_args__(cls) -> tuple:
        # Case-insensitive uniqueness: "Python" and "python" are the same
        # plant. A plain UniqueConstraint on (profile_id, name) is
        # case-sensitive and lets duplicates slip in, so this uses a
        # functional index over lower(name) instead. Supported by both
        # Postgres and SQLite (3.9+). Declared via declared_attr because a
        # functional index needs real column expressions (cls.name), which
        # only exist once the columns above are attached to the class.
        # This composite also covers lookups on profile_id alone, as its
        # leading column, so no separate index is needed there.
        return (
            Index(
                "uq_skill_name", cls.profile_id, func.lower(cls.name), unique=True
            ),
        )
