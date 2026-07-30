"""Interview Coach — the only stateful feature.

Every turn's prompt is rebuilt from rows in the database. The client sends one
thing: the text of its latest answer. It never sends the conversation history,
the interviewer's name, or the persona. Accepting any of those would let a
caller rewrite what the model believes has already happened, which is prompt
injection with extra steps.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.chains.interview_chain import build_interview_chain
from app.ai.schemas.interview_schema import ConversationTurn, InterviewLevel
from app.errors import AppError, NoCvOnProfile
from app.logging import get_logger
from app.models import CareerProfile, InterviewSession, InterviewTurn
from app.services import quota_service, xp_service

log = get_logger(__name__)

# Cost scales with turns, not sessions, so the quota is charged per turn and
# a session is additionally capped so one interview cannot run forever.
MAX_TURNS = 20
FEATURE = "interview_turn"


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


class SessionFinished(AppError):
    status_code = 409
    code = "session_finished"


class SessionTooLong(AppError):
    status_code = 409
    code = "session_too_long"


class NoPendingQuestion(AppError):
    status_code = 409
    code = "no_pending_question"


def _get_session(
    db: Session, profile_id: uuid.UUID, session_id: uuid.UUID
) -> InterviewSession:
    """Scoped in the WHERE clause: another user's session must look missing."""
    session = db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.profile_id == profile_id,
        )
    ).scalar_one_or_none()
    if session is None:
        raise ValueError(f"No interview session {session_id}")
    return session


def _history(db: Session, session_id: uuid.UUID) -> list[ConversationTurn]:
    """Rebuild the conversation from answered turns only.

    Read from the database, never from the request. This is the whole
    integrity story for the feature.
    """
    rows = db.execute(
        select(InterviewTurn)
        .where(
            InterviewTurn.session_id == session_id,
            InterviewTurn.answer.is_not(None),
        )
        .order_by(InterviewTurn.position)
    ).scalars()
    return [ConversationTurn(question=t.question, answer=t.answer or "") for t in rows]


def _invoke(
    *,
    cv_text: str,
    job_description: str,
    level: str,
    history: list[ConversationTurn],
    interviewer_name: str | None,
    session_id: uuid.UUID | None = None,
):
    """Call the chain from plain fields, not a persisted row.

    Taking values rather than a session lets `start` generate the first
    question *before* inserting anything, so a chain failure cannot leave a
    half-built session behind.
    """
    payload: dict = {
        "cv_text": cv_text,
        "job_description": job_description,
        "interview_level": level,
        "conversation_history": history,
    }
    if interviewer_name:
        payload["interviewer_name"] = interviewer_name

    try:
        return build_interview_chain().invoke(payload)
    except Exception as exc:
        log.exception(
            "interview_chain_failed",
            session_id=str(session_id) if session_id else None,
        )
        raise AnalysisFailed(
            "The interviewer could not respond. Try again shortly."
        ) from exc


def _append_question(
    db: Session, session: InterviewSession, result, position: int
) -> InterviewTurn:
    turn = InterviewTurn(
        session_id=session.id,
        profile_id=session.profile_id,
        position=position,
        question=result.current_question,
        difficulty=result.difficulty,
        expected_topics=list(result.expected_topics),
    )
    db.add(turn)
    return turn


def start(
    db: Session,
    profile_id: uuid.UUID,
    level: InterviewLevel | str,
    job_description: str,
) -> InterviewSession:
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")
    if not profile.cv_text:
        raise NoCvOnProfile(
            "Analyze your CV first — the interviewer asks about your real experience."
        )

    quota_service.consume(db, profile_id, FEATURE)

    level_value = InterviewLevel(level).value
    # Snapshot the CV: a later re-analysis must not change this interview.
    cv_text = profile.cv_text

    # Generate first, persist second. Nothing is written unless the model
    # actually produced a question.
    result = _invoke(
        cv_text=cv_text,
        job_description=job_description,
        level=level_value,
        history=[],
        interviewer_name=None,
    )

    session = InterviewSession(
        profile_id=profile_id,
        level=level_value,
        job_description=job_description,
        cv_text=cv_text,
        interviewer_name=result.interviewer_name,
    )
    db.add(session)
    db.flush()
    _append_question(db, session, result, position=0)

    db.commit()
    db.refresh(session)
    return session


def answer(
    db: Session,
    profile_id: uuid.UUID,
    session_id: uuid.UUID,
    text: str | None = None,
    audio_data: bytes | None = None,
) -> InterviewSession:
    """Record an answer to the open question and generate the next turn."""
    session = _get_session(db, profile_id, session_id)
    if session.finished:
        raise SessionFinished("That interview is already over.")

    pending = db.execute(
        select(InterviewTurn)
        .where(
            InterviewTurn.session_id == session.id,
            InterviewTurn.answer.is_(None),
        )
        .order_by(InterviewTurn.position)
        .limit(1)
    ).scalar_one_or_none()
    if pending is None:
        raise NoPendingQuestion("There is no open question to answer.")

    answered = db.execute(
        select(func.count(InterviewTurn.id)).where(
            InterviewTurn.session_id == session.id, InterviewTurn.answer.is_not(None)
        )
    ).scalar_one()
    if answered >= MAX_TURNS:
        raise SessionTooLong(
            f"This interview has reached its {MAX_TURNS}-question limit."
        )

    quota_service.consume(db, profile_id, FEATURE)

    if audio_data and not text:
        try:
            from app.services.audio_service import transcribe_audio
            transcribed = transcribe_audio(audio_data)
            if transcribed:
                pending.answer = transcribed
            else:
                raise ValueError("Audio transcription returned empty.")
        except Exception as exc:
            log.exception("stt_failed", session_id=str(session.id))
            raise AnalysisFailed(
                "Could not transcribe your audio. Try typing your answer instead."
            ) from exc
    elif text:
        pending.answer = text
    else:
        raise ValueError("Either text or audio_data must be provided.")
    db.flush()

    result = _invoke(
        cv_text=session.cv_text,
        job_description=session.job_description,
        level=session.level,
        history=_history(db, session.id),
        interviewer_name=session.interviewer_name,
        session_id=session.id,
    )

    # The chain evaluates the answer just given; attach it to that turn.
    if result.feedback_previous_answer is not None:
        pending.feedback = result.feedback_previous_answer.model_dump(mode="json")
    pending.score = result.score_previous_answer

    if result.interview_finished:
        session.finished = True
        if result.final_evaluation is not None:
            session.final_evaluation = result.final_evaluation.model_dump(mode="json")
        db.flush()
        xp_service.record_event(
            db,
            profile_id,
            "interview_completed",
            {
                "session_id": str(session.id),
                "level": session.level,
                "score": (session.final_evaluation or {}).get("overall_score"),
            },
            xp=xp_service.XP_AWARDS["interview_completed"],
        )
    else:
        _append_question(db, session, result, position=pending.position + 1)
        db.commit()

    db.refresh(session)
    return session


def get(
    db: Session, profile_id: uuid.UUID, session_id: uuid.UUID
) -> InterviewSession:
    return _get_session(db, profile_id, session_id)


def latest(db: Session, profile_id: uuid.UUID) -> InterviewSession | None:
    return db.execute(
        select(InterviewSession)
        .where(InterviewSession.profile_id == profile_id)
        .order_by(InterviewSession.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def list_sessions(db: Session, profile_id: uuid.UUID) -> list[InterviewSession]:
    return list(
        db.execute(
            select(InterviewSession)
            .where(InterviewSession.profile_id == profile_id)
            .order_by(InterviewSession.created_at.desc())
        ).scalars()
    )
