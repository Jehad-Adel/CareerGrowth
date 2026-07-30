import uuid

from sqlalchemy import Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class OfferEvaluation(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "offer_evaluations"
    __table_args__ = (
        Index("ix_offer_evaluations_profile_created", "profile_id", "created_at"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    offer_details: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict] = mapped_column(JSONType, nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation: Mapped[str] = mapped_column(
        String(50), nullable=False, default="", server_default=""
    )
