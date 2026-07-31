import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.quiz_chain import build_quiz_chain
from app.ai.sanitizer import sanitize_untrusted_text
from app.errors import AppError
from app.logging import get_logger
from app.models import QuizAttempt, QuizQuestion
from app.services import quota_service, xp_service

log = get_logger(__name__)

FEATURE = "quiz_generation"
PAGE_SIZE = 50


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


def generate(
    db: Session,
    profile_id: uuid.UUID,
    *,
    source_text: str,
    source_type: str = "manual",
    source_id: uuid.UUID | None = None,
    source_title: str = "",
    mastery_level: int = 1,
    num_questions: int = 5,
) -> QuizAttempt:
    num_questions = max(1, min(num_questions, 20))

    try:
        with quota_service.consume_and_refund_on_error(db, profile_id, FEATURE):
            result = build_quiz_chain().invoke(
                {
                    "source_text": sanitize_untrusted_text(
                        source_text, tag="source_text"
                    ),
                    "mastery_level": mastery_level,
                    "num_questions": num_questions,
                }
            )
    except AppError:
        raise
    except Exception as exc:
        log.exception("quiz_chain_failed", profile_id=str(profile_id))
        raise AnalysisFailed(
            "The quiz engine could not generate questions. Try again shortly."
        ) from exc

    attempt = QuizAttempt(
        profile_id=profile_id,
        source_type=source_type,
        source_id=source_id,
        source_title=source_title,
        mastery_level=mastery_level,
        total_questions=len(result.questions),
    )
    db.add(attempt)
    db.flush()

    for index, q in enumerate(result.questions):
        db.add(
            QuizQuestion(
                attempt_id=attempt.id,
                position=index,
                question=q.question,
                options=list(q.options),
                correct_answer=q.correct_answer,
                explanation=q.explanation,
            )
        )

    db.commit()
    db.refresh(attempt)
    return attempt


def submit_answers(
    db: Session,
    profile_id: uuid.UUID,
    attempt_id: uuid.UUID,
    answers: list[int],
) -> QuizAttempt:
    attempt = db.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.profile_id == profile_id,
        )
    ).scalar_one_or_none()
    if attempt is None:
        raise ValueError(f"No quiz attempt {attempt_id}")
    if attempt.completed_at is not None:
        raise ValueError("Quiz attempt already completed.")

    questions = list(
        db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.attempt_id == attempt.id)
            .order_by(QuizQuestion.position)
        ).scalars()
    )

    correct_count = 0
    for i, q in enumerate(questions):
        user_ans = answers[i] if i < len(answers) else -1
        q.user_answer = user_ans
        q.is_correct = user_ans == q.correct_answer
        if q.is_correct:
            correct_count += 1

    attempt.correct_count = correct_count
    attempt.score = (correct_count / len(questions) * 100) if questions else 0
    attempt.completed_at = datetime.now(timezone.utc)

    xp_service.record_event(
        db,
        profile_id,
        "quiz_completed",
        {
            "attempt_id": str(attempt.id),
            "score": attempt.score,
            "total": attempt.total_questions,
            "correct": correct_count,
        },
        xp=xp_service.XP_AWARDS.get("quiz_completed", 30),
    )

    db.commit()
    db.refresh(attempt)
    return attempt


def history(
    db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE
) -> list[QuizAttempt]:
    return list(
        db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.profile_id == profile_id)
            .order_by(QuizAttempt.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def get_attempt(
    db: Session, profile_id: uuid.UUID, attempt_id: uuid.UUID
) -> QuizAttempt | None:
    return db.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.profile_id == profile_id,
        )
    ).scalar_one_or_none()
