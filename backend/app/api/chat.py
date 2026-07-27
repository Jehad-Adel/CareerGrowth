import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import chat_service, quota_service, rag_service

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_QUESTION = 4_000


class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_QUESTION)


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list[dict] | None
    created_at: datetime


class ChatStateOut(BaseModel):
    messages: list[MessageOut]
    corpus_chunks: int
    messages_today: int
    daily_limit: int


def _to_out(m) -> MessageOut:
    return MessageOut(
        id=m.id,
        role=m.role,
        content=m.content,
        sources=m.sources,
        created_at=m.created_at,
    )


@router.get("", response_model=ChatStateOut)
def read_chat(profile: CurrentProfile, db: DbSession) -> ChatStateOut:
    used = quota_service.usage_today(db, profile.id)
    return ChatStateOut(
        messages=[_to_out(m) for m in chat_service.history(db, profile.id)],
        corpus_chunks=rag_service.corpus_size(db, profile.id),
        messages_today=used.get(chat_service.FEATURE, 0),
        daily_limit=quota_service.DAILY_LIMITS[chat_service.FEATURE],
    )


@router.post("", response_model=MessageOut)
@limiter.limit("20/minute")
def ask(
    request: Request,
    payload: AskRequest,
    profile: CurrentProfile,
    db: DbSession,
) -> MessageOut:
    reply = chat_service.send(db, profile, payload.message)
    return _to_out(reply)
