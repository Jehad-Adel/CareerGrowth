import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.chat_chain import build_chat_chain
from app.errors import AppError
from app.logging import get_logger
from app.models import CareerProfile, ChatMessage, Skill
from app.services import quota_service, rag_service

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
    """Oldest-first page of the conversation."""
    rows = list(
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.profile_id == profile_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        ).scalars()
    )
    return list(reversed(rows))


def _history_block(messages: list[ChatMessage]) -> str:
    if not messages:
        return "No earlier turns."
    recent = messages[-HISTORY_TURNS:]
    return "\n".join(f"{m.role}: {m.content}" for m in recent)


def send(db: Session, profile: CareerProfile, question: str) -> ChatMessage:
    """Answer a question, grounded in this person's own documents."""
    quota_service.consume(db, profile.id, FEATURE)

    prior = history(db, profile.id)
    chunks = rag_service.retrieve(db, profile.id, question)

    try:
        answer = build_chat_chain().invoke(
            {
                "profile": _profile_block(db, profile),
                "context": rag_service.build_context(chunks),
                "history": _history_block(prior),
                "question": question,
            }
        )
    except Exception as exc:
        log.exception("chat_chain_failed", profile_id=str(profile.id))
        raise AnalysisFailed(
            "The assistant could not answer that. Try again shortly."
        ) from exc

    # Persist both turns only after a successful answer, so a failure does not
    # leave a question hanging with no reply.
    db.add(
        ChatMessage(profile_id=profile.id, role="user", content=question)
    )
    reply = ChatMessage(
        profile_id=profile.id,
        role="assistant",
        content=answer.strip(),
        sources=[
            {"kind": c.document.kind, "chunk": c.chunk_index} for c in chunks
        ],
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply
