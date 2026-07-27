import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.schemas.interview_schema import (
    AnswerFeedback,
    FinalEvaluation,
    InterviewLevel,
    InterviewResponse,
)
from app.auth import AuthUser
from app.db import Base
from app.errors import NoCvOnProfile, QuotaExceeded
from app.models import CareerProfile, GrowthEvent, InterviewSession, InterviewTurn
from app.services import interview_service, profile_service, quota_service

JD = "Backend engineer. Python, FastAPI, Postgres, Kubernetes. " * 3


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _profile(db: Session, cv: str = "Nour, Python engineer.") -> CareerProfile:
    p = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    p.cv_text = cv
    db.commit()
    return p


def _response(
    question="Tell me about FastAPI.",
    name="Dana Reyes",
    finished=False,
    feedback=True,
    score=70,
) -> InterviewResponse:
    return InterviewResponse(
        interviewer_name=name,
        interview_level=InterviewLevel.TECHNICAL_LEAD,
        current_question=question,
        follow_up_question=None,
        expected_topics=["ASGI", "dependency injection"],
        difficulty="Medium",
        feedback_previous_answer=(
            AnswerFeedback(
                strengths=["Clear"],
                weaknesses=["Shallow"],
                missing_concepts=["ASGI"],
                confidence_level=60,
                technical_accuracy=55,
                communication_score=70,
            )
            if feedback
            else None
        ),
        score_previous_answer=score,
        interview_finished=finished,
        final_evaluation=(
            FinalEvaluation(
                overall_score=68,
                technical_skills=65,
                communication=72,
                confidence=66,
                problem_solving=70,
                weak_areas=["Containers"],
                strong_areas=["Python"],
                hiring_recommendation="Hire",
                summary="Solid mid-level candidate.",
            )
            if finished
            else None
        ),
    )


class _Chain:
    """Records every payload the service sends to the model."""

    calls: list[dict] = []
    script: list[InterviewResponse] = []
    error: Exception | None = None

    def invoke(self, payload):
        _Chain.calls.append(payload)
        if _Chain.error:
            raise _Chain.error
        return _Chain.script.pop(0) if _Chain.script else _response()


def _patch(monkeypatch, script=None, error=None):
    _Chain.calls = []
    _Chain.script = list(script or [])
    _Chain.error = error
    monkeypatch.setattr(interview_service, "build_interview_chain", lambda: _Chain())
    return _Chain


# --- Guards ---


def test_start_requires_a_cv(monkeypatch):
    db = _session()
    p = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch)
    with pytest.raises(NoCvOnProfile):
        interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)


def test_missing_cv_checked_before_quota(monkeypatch):
    db = _session()
    p = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch)
    with pytest.raises(NoCvOnProfile):
        interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    assert quota_service.usage_today(db, p.id) == {}


# --- Starting ---


def test_start_creates_a_session_with_one_open_question(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch)

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)

    assert s.interviewer_name == "Dana Reyes"
    assert s.finished is False
    assert len(s.turns) == 1
    assert s.turns[0].answer is None
    assert s.turns[0].position == 0


def test_start_snapshots_the_cv(monkeypatch):
    """Re-analyzing a CV mid-interview must not change the interview."""
    db = _session()
    p = _profile(db, cv="ORIGINAL CV")
    _patch(monkeypatch)

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    p.cv_text = "COMPLETELY DIFFERENT CV"
    db.commit()

    interview_service.answer(db, p.id, s.id, "An answer.")
    assert _Chain.calls[-1]["cv_text"] == "ORIGINAL CV"


# --- The integrity rule ---


def test_history_is_rebuilt_from_the_database(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(
        monkeypatch,
        script=[_response(question="Q1"), _response(question="Q2"), _response(question="Q3")],
    )

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")
    interview_service.answer(db, p.id, s.id, "A2")

    history = _Chain.calls[-1]["conversation_history"]
    assert [(t.question, t.answer) for t in history] == [("Q1", "A1"), ("Q2", "A2")]


def test_interviewer_name_is_threaded_and_stable(monkeypatch):
    """The persona must not rename itself mid-interview."""
    db = _session()
    p = _profile(db)
    _patch(
        monkeypatch,
        script=[
            _response(name="Dana Reyes"),
            _response(name="IMPOSTOR"),
            _response(name="ANOTHER"),
        ],
    )

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")

    # Every follow-up call carries the original name back in.
    assert _Chain.calls[-1]["interviewer_name"] == "Dana Reyes"
    db.refresh(s)
    assert s.interviewer_name == "Dana Reyes"


def test_answer_only_accepts_its_own_text(monkeypatch):
    """The service signature takes text, not history — nothing else is client-set."""
    db = _session()
    p = _profile(db)
    _patch(monkeypatch)
    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)

    interview_service.answer(db, p.id, s.id, "my answer")
    payload = _Chain.calls[-1]
    assert payload["job_description"] == JD
    assert payload["interview_level"] == "technical_lead"


# --- Answering ---


def test_answer_records_feedback_on_the_answered_turn(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch, script=[_response(question="Q1"), _response(question="Q2")])

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")
    db.refresh(s)

    first = s.turns[0]
    assert first.answer == "A1"
    assert first.score == 70
    assert first.feedback["technical_accuracy"] == 55
    assert len(s.turns) == 2
    assert s.turns[1].answer is None


def test_finishing_persists_the_evaluation_and_emits_an_event(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch, script=[_response(), _response(finished=True)])

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")
    db.refresh(s)

    assert s.finished is True
    assert s.final_evaluation["overall_score"] == 68
    assert db.query(GrowthEvent).filter_by(type="interview_completed").count() == 1
    # No dangling unanswered question after the interview ends.
    assert all(t.answer is not None for t in s.turns)


def test_answering_a_finished_session_is_rejected(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch, script=[_response(), _response(finished=True)])

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")

    with pytest.raises(interview_service.SessionFinished) as exc:
        interview_service.answer(db, p.id, s.id, "A2")
    assert exc.value.status_code == 409


def test_turn_cap_is_enforced(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch)
    monkeypatch.setattr(interview_service, "MAX_TURNS", 2)
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "interview_turn", 999)

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")
    interview_service.answer(db, p.id, s.id, "A2")

    with pytest.raises(interview_service.SessionTooLong):
        interview_service.answer(db, p.id, s.id, "A3")


def test_quota_is_charged_per_turn_not_per_session(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch)
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "interview_turn", 3)

    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    interview_service.answer(db, p.id, s.id, "A1")
    interview_service.answer(db, p.id, s.id, "A2")

    with pytest.raises(QuotaExceeded):
        interview_service.answer(db, p.id, s.id, "A3")
    assert quota_service.usage_today(db, p.id)["interview_turn"] == 3


# --- Isolation and failure ---


def test_another_users_session_looks_missing(monkeypatch):
    db = _session()
    mine = _profile(db)
    theirs = _profile(db)
    _patch(monkeypatch)
    s = interview_service.start(db, mine.id, InterviewLevel.TECHNICAL_LEAD, JD)

    with pytest.raises(ValueError, match="No interview session"):
        interview_service.answer(db, theirs.id, s.id, "sneaky")
    with pytest.raises(ValueError, match="No interview session"):
        interview_service.get(db, theirs.id, s.id)


def test_chain_failure_is_a_clean_502(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch, error=RuntimeError("gemini key sk-leak"))

    with pytest.raises(interview_service.AnalysisFailed) as exc:
        interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)
    assert "sk-leak" not in exc.value.message
    assert db.query(InterviewSession).count() == 0


def test_latest_is_scoped(monkeypatch):
    db = _session()
    mine = _profile(db)
    theirs = _profile(db)
    _patch(monkeypatch)
    interview_service.start(db, mine.id, InterviewLevel.FRIENDLY_HR, JD)

    assert interview_service.latest(db, mine.id) is not None
    assert interview_service.latest(db, theirs.id) is None


def test_no_pending_question_is_rejected(monkeypatch):
    db = _session()
    p = _profile(db)
    _patch(monkeypatch)
    s = interview_service.start(db, p.id, InterviewLevel.TECHNICAL_LEAD, JD)

    db.query(InterviewTurn).filter_by(session_id=s.id).update({"answer": "done"})
    db.commit()

    with pytest.raises(interview_service.NoPendingQuestion):
        interview_service.answer(db, p.id, s.id, "extra")
