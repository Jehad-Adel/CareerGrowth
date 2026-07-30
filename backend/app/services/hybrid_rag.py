"""Utility for hybrid RAG — retrieves from both personal and curated corpora
and builds a combined context string for prompt injection.

This is called by feature services BEFORE they invoke their LLM chain.
"""

import uuid

from sqlalchemy.orm import Session

from app.ai import embeddings
from app.logging import get_logger
from app.services import knowledge_service, rag_service

log = get_logger(__name__)

MAX_HYBRID_CONTEXT_CHARS = 6_000


def retrieve_context(
    db: Session,
    profile_id: uuid.UUID,
    query: str,
    *,
    max_chars: int = MAX_HYBRID_CONTEXT_CHARS,
) -> str:
    """Retrieve relevant context from both personal documents and curated
    knowledge base for the given query.

    Args:
        query: The text to retrieve context for (e.g. job description, CV text).
        max_chars: Maximum characters for the combined context.

    Returns:
        A formatted context string ready to inject into a prompt, or empty string
        if nothing was found.
    """
    if not query.strip():
        return ""

    try:
        query_vector = embeddings.embed_query(query)
    except Exception:
        log.exception("embedding_failed", query_preview=query[:100])
        return ""

    parts: list[str] = []
    budget = max_chars

    # Personal documents
    try:
        personal_chunks = rag_service.retrieve(
            db, profile_id, query, k=3, vector=query_vector
        )
        personal_ctx = rag_service.build_context(personal_chunks)
        if personal_ctx and personal_ctx != "No documents have been indexed for this person yet.":
            if len(personal_ctx) <= budget:
                parts.append(f"[Your Documents]\n{personal_ctx}")
                budget -= len(personal_ctx)
    except Exception:
        log.exception("personal_rag_failed", profile_id=str(profile_id))

    # Curated knowledge base
    try:
        curated_chunks = knowledge_service.retrieve(
            db, query, k=3, vector=query_vector
        )
        curated_ctx = knowledge_service.build_context(curated_chunks)
        if curated_ctx:
            if len(curated_ctx) <= budget:
                parts.append(f"[CareerFarm Guidance]\n{curated_ctx}")
    except Exception:
        log.exception("knowledge_rag_failed")

    if not parts:
        return ""

    return "\n\n".join(parts)
