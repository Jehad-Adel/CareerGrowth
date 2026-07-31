import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.ai.chains.chat_chain import build_chat_chain
from app.errors import AppError
from app.logging import get_logger
from app.models import (
    CareerProfile,
    ChatMessage,
    DocumentChunk,
    KnowledgeChunk,
    Skill,
)
from app.services import knowledge_service, quota_service, rag_service

log = get_logger(__name__)

FEATURE = "chat_message"

# How much prior conversation goes into the prompt. Unbounded history would
# grow the cost of every turn without improving the answer.
HISTORY_TURNS = 8
# What the page loads.
PAGE_SIZE = 50


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


def _profile_block(db: Session, profile: CareerProfile) -> str:
    skills = db.execute(
        select(Skill).where(Skill.profile_id == profile.id).order_by(
            Skill.mastery.desc()
        )
    ).scalars()
    lines = [
        f"Name: {profile.full_name or 'unknown'}",
        f"Current role: {profile.current_role or 'unknown'}",
        f"Target role: {profile.target_role or 'not set'}",
        f"Seniority: {profile.seniority_level or 'unknown'}",
        f"Level {profile.level} with {profile.xp} XP",
    ]
    named = [f"{s.name} ({s.mastery}%)" for s in skills]
    lines.append(f"Skills: {', '.join(named) if named else 'none recorded yet'}")
    return "\n".join(lines)


def history(db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE) -> list[ChatMessage]:
    """Oldest-first page of the conversation, most recent `limit` turns.

    Ordered by `position`, never `created_at` — see the model for why that
    column cannot separate a question from its own answer.
    """
    rows = list(
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.profile_id == profile_id)
            .order_by(ChatMessage.position.desc())
            .limit(limit)
        ).scalars()
    )
    return list(reversed(rows))


def clear_history(db: Session, profile_id: uuid.UUID) -> int:
    result = db.execute(delete(ChatMessage).where(ChatMessage.profile_id == profile_id))
    db.commit()
    return result.rowcount


def _next_position(db: Session, profile_id: uuid.UUID) -> int:
    """One past the last turn. Concurrency is bounded by the quota row lock."""
    highest = db.execute(
        select(func.max(ChatMessage.position)).where(
            ChatMessage.profile_id == profile_id
        )
    ).scalar_one()
    return 0 if highest is None else highest + 1


def _sources(
    chunks: list[DocumentChunk], guides: list[KnowledgeChunk]
) -> list[dict]:
    """What grounded this reply, for the "why did it say that" line.

    Both corpora are recorded. Attributing only the personal documents was
    misleading once curated guidance started shaping answers: a reply built
    entirely from the ATS rules showed no source at all.

    `origin` separates them because they mean different things to a reader —
    "your CV" is evidence about them, "CareerGrowth guidance" is not.
    """
    return [
        {
            "origin": "document",
            "kind": chunk.document.kind,
            "label": chunk.document.kind,
            "chunk": chunk.chunk_index,
        }
        for chunk in chunks
    ] + [
        {
            "origin": "guide",
            "kind": "guide",
            "label": guide.category,
            "title": guide.title,
        }
        for guide in guides
    ]


def _history_block(messages: list[ChatMessage]) -> str:
    if not messages:
        return "No earlier turns."
    recent = messages[-HISTORY_TURNS:]
    return "\n".join(f"{m.role}: {m.content}" for m in recent)


def send(db: Session, profile: CareerProfile, question: str) -> ChatMessage:
    """Answer a question, grounded in this person's own documents."""
    prior = history(db, profile.id)

    # Two corpora, one question, one embedding. Letting each retrieval embed
    # the question itself costs a second network round trip to Google for a
    # byte-identical vector, on the hot path of every chat turn.
    question_vector = embeddings.embed_query(question) if question.strip() else None
    chunks = rag_service.retrieve(db, profile.id, question, vector=question_vector)

    # The curated corpus is a separate *ranking*, though, not extra rows in
    # the same one. A single top-k over both lets a well-phrased general rule
    # evict the document the question was actually about — and the two answer
    # different halves of a career question anyway.
    #
    # Best-effort: an empty or unreachable corpus degrades the answer, it does
    # not fail the turn the user already paid a quota call for.
    try:
        guides = knowledge_service.retrieve(db, question, vector=question_vector)
    except Exception:
        log.exception("knowledge_retrieve_failed", profile_id=str(profile.id))
        guides = []
    guidance = knowledge_service.build_context(guides)

    try:
        with quota_service.consume_and_refund_on_error(db, profile.id, FEATURE):
            answer = build_chat_chain().invoke(
                {
                    "profile": _profile_block(db, profile),
                    "context": rag_service.build_context(chunks),
                    "guidance": guidance or "No curated guidance matched this question.",
                    "history": _history_block(prior),
                    "question": question,
                }
            )
    except AppError:
        raise
    except Exception as exc:
        log.exception("chat_chain_failed", profile_id=str(profile.id))
        raise AnalysisFailed(
            "The assistant could not answer that. Try again shortly."
        ) from exc

    # Persist both turns only after a successful answer, so a failure does not
    # leave a question hanging with no reply. The question takes the lower
    # position: it was asked first and must render first.
    position = _next_position(db, profile.id)
    db.add(
        ChatMessage(
            profile_id=profile.id,
            position=position,
            role="user",
            content=question,
        )
    )
    reply = ChatMessage(
        profile_id=profile.id,
        position=position + 1,
        role="assistant",
        content=answer.strip(),
        sources=_sources(chunks, guides),
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply
