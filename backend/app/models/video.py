import uuid

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class VideoSummary(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "video_summaries"
    __table_args__ = (
        Index("ix_video_summaries_profile_created", "profile_id", "created_at"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, default="", server_default=""
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="youtube"
    )
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="summary"
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    key_takeaways: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
