from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.ai.embeddings import DIMENSIONS
from app.db import Base
from app.models.base import UUIDPrimaryKey


class KnowledgeChunk(UUIDPrimaryKey, Base):
    """One embedded slice of the curated `knowledge_base/` corpus.

    Deliberately has no `profile_id`: this is editorial content the team
    writes, identical for every user, and it is the one corpus in the system
    that is not owned by anybody. Retrieval against it therefore does *not*
    filter by profile — which is safe only because nothing user-supplied is
    ever written here. Ingestion runs from a CLI against files in the repo,
    never from a request.

    There is no parent `knowledge_documents` table on purpose. A personal
    document needs one because it is derived from a row that can be re-run and
    replaced; a corpus entry's identity is just its file and its position in
    it, which these two columns already carry.
    """

    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        # Re-ingesting a file overwrites its entries in place rather than
        # appending a second copy of the corpus.
        UniqueConstraint("source", "chunk_index", name="uq_knowledge_chunks_source_idx"),
        Index("ix_knowledge_chunks_category", "category"),
    )

    # Top-level folder under knowledge_base/, e.g. "ATS", "CV Writing".
    # Doubles as the label the chat cites.
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    # Path relative to the corpus root, so a bad entry traces to its file.
    source: Mapped[str] = mapped_column(String(300), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # SHA-256 of the embedded text. Lets a re-ingest skip unchanged entries
    # instead of paying the embedding API for a corpus that did not move.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSIONS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
