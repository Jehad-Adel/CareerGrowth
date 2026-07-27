"""Ingest and retrieval for Career Chat.

The corpus builds itself from what the other features already produce: a CV
analysis, a job match, a skill gap, a roadmap. Nothing here asks the user to
upload anything twice.
"""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.logging import get_logger
from app.models import Document, DocumentChunk

log = get_logger(__name__)

# Roughly 800 tokens at ~4 chars/token, with overlap so a fact spanning a
# boundary is still retrievable from at least one chunk.
CHUNK_CHARS = 3_200
OVERLAP_CHARS = 400

TOP_K = 5
# Bounds how much retrieved text reaches the prompt. Without this, five long
# chunks could dominate the context window and push out the actual question.
MAX_CONTEXT_CHARS = 8_000


def chunk_text(text: str) -> list[str]:
    """Split on paragraph boundaries where possible, with overlap."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= CHUNK_CHARS:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            # Prefer a paragraph break, then a sentence end, then a hard cut.
            for sep in ("\n\n", ". "):
                found = text.rfind(sep, start + CHUNK_CHARS // 2, end)
                if found != -1:
                    end = found + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - OVERLAP_CHARS, start + 1)
    return chunks


def ingest(
    db: Session,
    profile_id: uuid.UUID,
    kind: str,
    content: str,
    *,
    title: str | None = None,
    source_id: uuid.UUID | None = None,
) -> Document | None:
    """Chunk, embed, and store a document. Replaces any earlier version.

    Returns None when there is nothing worth embedding, so callers can ingest
    unconditionally without guarding every call site.
    """
    chunks = chunk_text(content)
    if not chunks:
        return None

    # Replacing rather than appending keeps a re-analysis from leaving stale
    # chunks that contradict the current ones.
    if source_id is not None:
        db.execute(
            delete(Document).where(
                Document.profile_id == profile_id,
                Document.kind == kind,
                Document.source_id == source_id,
            )
        )
    else:
        db.execute(
            delete(Document).where(
                Document.profile_id == profile_id, Document.kind == kind
            )
        )

    vectors = embeddings.embed_documents(chunks)

    document = Document(
        profile_id=profile_id, kind=kind, title=title, source_id=source_id
    )
    db.add(document)
    db.flush()

    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        db.add(
            DocumentChunk(
                document_id=document.id,
                profile_id=profile_id,
                chunk_index=index,
                content=chunk,
                embedding=vector,
            )
        )

    db.commit()
    log.info(
        "rag_ingested", kind=kind, chunks=len(chunks), profile_id=str(profile_id)
    )
    db.refresh(document)
    return document


def retrieve(
    db: Session, profile_id: uuid.UUID, query: str, k: int = TOP_K
) -> list[DocumentChunk]:
    """Top-k chunks for this query, belonging to this profile.

    The profile filter is in the SQL WHERE clause, evaluated alongside the
    vector ordering — never applied to an already-computed top-k. Post-
    filtering would mean another user's chunks could consume the k slots, and
    a bug in the filter would surface their content rather than nothing.
    """
    if not query.strip():
        return []

    vector = embeddings.embed_query(query)
    return list(
        db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.profile_id == profile_id)
            .order_by(DocumentChunk.embedding.cosine_distance(vector))
            .limit(k)
        ).scalars()
    )


def build_context(chunks: list[DocumentChunk]) -> str:
    """Render retrieved chunks as delimited, labelled text for the prompt."""
    if not chunks:
        return "No documents have been indexed for this person yet."

    parts: list[str] = []
    budget = MAX_CONTEXT_CHARS
    for chunk in chunks:
        body = chunk.content[:budget]
        if not body:
            break
        parts.append(f"[{chunk.document.kind} #{chunk.chunk_index}]\n{body}")
        budget -= len(body)
        if budget <= 0:
            break
    return "\n\n".join(parts)


def corpus_size(db: Session, profile_id: uuid.UUID) -> int:
    """How many chunks this profile has indexed. Drives the empty state."""
    return db.execute(
        select(func.count(DocumentChunk.id)).where(
            DocumentChunk.profile_id == profile_id
        )
    ).scalar_one()
