import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class InterviewSession(UUIDPrimaryKey, Timestamps, Base):
    """One mock interview, spanning many turns."""

    __tablename__ = "interview_sessions"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # friendly_hr | technical_lead | stress_interview
    level: Mapped[str] = mapped_column(String(30), nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    # Threaded back into every turn so the persona cannot rename itself
    # mid-interview. Null only before the first question is generated.
    interviewer_name: Mapped[str | None] = mapped_column(String(120))
    # Snapshot of the CV at session start. An interview must not change
    # character because the user re-analyzed their CV halfway through.
    cv_text: Mapped[str] = mapped_column(Text, nullable=False)

    finished: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    final_evaluation: Mapped[dict | None] = mapped_column(JSONType)

    turns: Mapped[list["InterviewTurn"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewTurn.position",
        lazy="selectin",
    )


class InterviewTurn(UUIDPrimaryKey, Timestamps, Base):
    """One question, and the answer to it once given.

    A turn is created with a question and no answer; answering fills it in and
    produces the next turn. That is why `answer` is nullable.
    """

    __tablename__ = "interview_turns"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalised so a turn can be authorized without joining the session.
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(10))
    expected_topics: Mapped[list] = mapped_column(
        JSONType, nullable=False, default=list, server_default="[]"
    )

    answer: Mapped[str | None] = mapped_column(Text)
    # Evaluation of THIS turn's answer, produced when the next turn is generated.
    feedback: Mapped[dict | None] = mapped_column(JSONType)
    score: Mapped[int | None] = mapped_column(Integer)

    session: Mapped["InterviewSession"] = relationship(back_populates="turns")
