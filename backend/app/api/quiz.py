import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import quiz_service

router = APIRouter(tags=["quiz"])


class QuizGenerateIn(BaseModel):
    source_text: str = Field(min_length=10, max_length=50_000)
    source_type: str = Field(default="manual", max_length=40)
    source_id: str | None = None
    source_title: str = Field(default="", max_length=300)
    mastery_level: int = Field(default=1, ge=1, le=5)
    num_questions: int = Field(default=5, ge=1, le=20)


class QuizAnswerIn(BaseModel):
    answers: list[int] = Field(min_length=1, max_length=20)


class QuizQuestionOut(BaseModel):
    id: str
    position: int
    question: str
    options: list[str]
    correct_answer: int | None = None
    explanation: str | None = None
    user_answer: int | None = None
    is_correct: bool | None = None


class QuizAttemptOut(BaseModel):
    id: str
    source_type: str
    source_title: str
    mastery_level: int
    score: float | None
    total_questions: int
    correct_count: int
    completed_at: datetime | None
    created_at: datetime
    questions: list[QuizQuestionOut]


def _question_out(q) -> QuizQuestionOut:
    return QuizQuestionOut(
        id=str(q.id),
        position=q.position,
        question=q.question,
        options=list(q.options),
        correct_answer=q.correct_answer if q.user_answer is not None else None,
        explanation=q.explanation if q.user_answer is not None else None,
        user_answer=q.user_answer,
        is_correct=q.is_correct,
    )


def _attempt_out(a) -> QuizAttemptOut:
    return QuizAttemptOut(
        id=str(a.id),
        source_type=a.source_type,
        source_title=a.source_title,
        mastery_level=a.mastery_level,
        score=a.score,
        total_questions=a.total_questions,
        correct_count=a.correct_count,
        completed_at=a.completed_at,
        created_at=a.created_at,
        questions=[_question_out(q) for q in a.questions],
    )


@router.post("/quiz/generate", response_model=QuizAttemptOut)
@limiter.limit("10/minute")
def generate_quiz(
    request: Request,
    payload: QuizGenerateIn,
    profile: CurrentProfile,
    db: DbSession,
) -> QuizAttemptOut:
    attempt = quiz_service.generate(
        db,
        profile.id,
        source_text=payload.source_text,
        source_type=payload.source_type,
        source_id=uuid.UUID(payload.source_id) if payload.source_id else None,
        source_title=payload.source_title,
        mastery_level=payload.mastery_level,
        num_questions=payload.num_questions,
    )
    return _attempt_out(attempt)


@router.post("/quiz/attempts/{attempt_id}/submit", response_model=QuizAttemptOut)
def submit_quiz(
    attempt_id: uuid.UUID,
    payload: QuizAnswerIn,
    profile: CurrentProfile,
    db: DbSession,
) -> QuizAttemptOut:
    attempt = quiz_service.submit_answers(
        db, profile.id, attempt_id, payload.answers
    )
    return _attempt_out(attempt)


@router.get("/quiz/history", response_model=list[QuizAttemptOut])
def quiz_history(
    profile: CurrentProfile,
    db: DbSession,
) -> list[QuizAttemptOut]:
    return [_attempt_out(a) for a in quiz_service.history(db, profile.id)]


@router.get("/quiz/attempts/{attempt_id}", response_model=QuizAttemptOut)
def get_quiz_attempt(
    attempt_id: uuid.UUID,
    profile: CurrentProfile,
    db: DbSession,
) -> QuizAttemptOut:
    attempt = quiz_service.get_attempt(db, profile.id, attempt_id)
    if attempt is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    return _attempt_out(attempt)
