import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import BigIntegerType, JSONType


class GrowthEvent(Base):
    """Append-only from the application's side: individual events are never
    updated or deleted. The whole log is hard-deleted along with its
    profile via the FK's ondelete="CASCADE" — that's intended, since
    account deletion must purge user data. The Farm reads this."""

    __tablename__ = "growth_events"
    __table_args__ = (
        Index("ix_growth_events_profile_created", "profile_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigIntegerType, primary_key=True, autoincrement=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # skill_discovered | skill_leveled | goal_completed | cv_analyzed
    # | job_matched | gap_analyzed | roadmap_created | interview_completed
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSONType, nullable=False, default=dict, server_default="{}"
    )
    xp_awarded: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
