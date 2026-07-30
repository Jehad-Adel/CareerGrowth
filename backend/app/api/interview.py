import uuid
from datetime import datetime

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel, Field

from app.ai.schemas.interview_schema import InterviewLevel
from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import interview_service

router = APIRouter(prefix="/interview", tags=["interview"])

MIN_JD = 50
MAX_JD = 20_000
MAX_ANSWER = 8_000


class StartRequest(BaseModel):
    level: InterviewLevel
    job_description: str = Field(min_length=MIN_JD, max_length=MAX_JD)


class AnswerRequest(BaseModel):
    # The ONLY thing the client contributes to the next prompt. History,
    # persona, and interviewer name all come from the database.
    answer: str = Field(min_length=1, max_length=MAX_ANSWER)


class TurnOut(BaseModel):
    id: uuid.UUID
    position: int
    question: str
    difficulty: str | None
    expected_topics: list[str]
    answer: str | None
    feedback: dict | None
    score: int | None


class SessionOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    level: str
    interviewer_name: str | None
    finished: bool
    final_evaluation: dict | None
    turns: list[TurnOut]


def _to_out(session) -> SessionOut:
    return SessionOut(
        id=session.id,
        created_at=session.created_at,
        level=session.level,
        interviewer_name=session.interviewer_name,
        finished=session.finished,
        final_evaluation=session.final_evaluation,
        turns=[
            TurnOut(
                id=t.id,
                position=t.position,
                question=t.question,
                difficulty=t.difficulty,
                expected_topics=list(t.expected_topics),
                answer=t.answer,
                feedback=t.feedback,
                score=t.score,
            )
            for t in session.turns
        ],
    )


@router.post("/sessions", response_model=SessionOut)
@limiter.limit("5/minute")
def start_session(
    request: Request,
    payload: StartRequest,
    profile: CurrentProfile,
    db: DbSession,
) -> SessionOut:
    session = interview_service.start(
        db, profile.id, payload.level, payload.job_description
    )
    return _to_out(session)


@router.post("/sessions/{session_id}/answer", response_model=SessionOut)
@limiter.limit("20/minute")
async def answer_question(
    request: Request,
    session_id: uuid.UUID,
    profile: CurrentProfile,
    db: DbSession,
    answer: str = Form(default="", max_length=MAX_ANSWER),
    audio: UploadFile | None = File(default=None),
) -> SessionOut:
    audio_bytes = await audio.read() if audio else None
    text = answer if answer else None
    session = interview_service.answer(
        db, profile.id, session_id, text=text, audio_data=audio_bytes
    )
    return _to_out(session)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(profile: CurrentProfile, db: DbSession) -> list[SessionOut]:
    return [_to_out(s) for s in interview_service.list_sessions(db, profile.id)]


@router.get("/sessions/{session_id}", response_model=SessionOut)
def read_session(
    session_id: uuid.UUID, profile: CurrentProfile, db: DbSession
) -> SessionOut:
    return _to_out(interview_service.get(db, profile.id, session_id))


@router.get("/latest", response_model=SessionOut | None)
def latest_session(profile: CurrentProfile, db: DbSession) -> SessionOut | None:
    session = interview_service.latest(db, profile.id)
    return _to_out(session) if session else None
