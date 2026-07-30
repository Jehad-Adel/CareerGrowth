import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class QuizAttempt(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("ix_quiz_attempts_profile_created", "profile_id", "created_at"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default="manual"
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    source_title: Mapped[str] = mapped_column(
        String(300), nullable=False, default=""
    )
    mastery_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    correct_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.position",
        lazy="selectin",
    )


class QuizQuestion(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        Index("ix_quiz_questions_attempt", "attempt_id"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    user_answer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    explanation: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )

    attempt: Mapped["QuizAttempt"] = relationship(back_populates="questions")
