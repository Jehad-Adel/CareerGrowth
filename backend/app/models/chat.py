import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.ai.embeddings import DIMENSIONS
from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class ChatMessage(UUIDPrimaryKey, Base):
    """One turn of conversation. Append-only, like growth events."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_profile_created", "profile_id", "created_at"),
        Index("ix_chat_messages_profile_position", "profile_id", "position"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # Conversation order, assigned by chat_service.
    #
    # `created_at` cannot carry it: func.now() is transaction start time in
    # Postgres, so a question and its reply -- written in one transaction --
    # get identical timestamps, and a UUIDv4 primary key breaks no ties.
    # Ordering on created_at alone can put the answer before the question.
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # user | assistant
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Which chunks grounded an assistant reply, for "why did it say that".
    sources: Mapped[list | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Document(UUIDPrimaryKey, Timestamps, Base):
    """A source the chat can cite: a CV, a job description, a roadmap."""

    __tablename__ = "documents"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # cv | job_match | skill_gap | roadmap
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    # The row this was derived from, so a re-ingest can replace it cleanly.
    source_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(UUIDPrimaryKey, Base):
    """An embedded slice of a document."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Denormalised so retrieval can filter by owner in the same WHERE clause as
    # the vector search. Post-filtering a top-k result set would let one user's
    # chunks crowd out their own results -- or surface someone else's.
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSIONS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")
