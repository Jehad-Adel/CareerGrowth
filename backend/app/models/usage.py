import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import BigIntegerType


class AiUsage(Base):
    """One row per (profile, day, feature). Backs the daily AI quota."""

    __tablename__ = "ai_usage"
    __table_args__ = (
        UniqueConstraint("profile_id", "day", "feature", name="uq_ai_usage_slot"),
    )

    id: Mapped[int] = mapped_column(BigIntegerType, primary_key=True, autoincrement=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    feature: Mapped[str] = mapped_column(String(40), nullable=False)
    calls: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
