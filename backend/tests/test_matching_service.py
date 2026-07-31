import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.schemas.cover_letter_schema import CoverLetter as CoverLetterResult
from app.ai.schemas.job_match_schema import JobMatch as JobMatchResult
from app.ai.schemas.resume_optimizer_schema import ResumeOptimization as ResumeResult
from app.ai.schemas.resume_optimizer_schema import ResumeSection
from app.ai.schemas.skill_gap_schema import SkillGapAnalysis as GapResult
from app.ai.schemas.skill_gap_schema import SkillGapItem
from app.auth import AuthUser
from app.db import Base
from app.errors import NoCvOnProfile, QuotaExceeded
from app.models import (
    CareerProfile,
    CoverLetter as CoverLetterRecord,
    GrowthEvent,
    JobMatch,
    ResumeOptimization,
    Skill,
    SkillGapAnalysis,
)
from app.services import matching_service, profile_service, quota_service

JD = "We need a backend engineer with Kubernetes, Go, and PostgreSQL. " * 3


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _profile_with_cv(db: Session, cv_text: str = "Nour, Python engineer.") -> CareerProfile:
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    profile.cv_text = cv_text
    db.commit()
    return profile


def _match_result(**over) -> JobMatchResult:
    return JobMatchResult(
        **{
            "match_score": 62,
            "hiring_probability": 55,
            "hiring_probability_reasoning": "Strong Python, no infra.",
            "skill_matches": [
                {
                    "job_skill": "Python",
                    "requirement_level": "Required",
                    "matched": True,
                    "matched_via": "Python engineer",
                },
                {
                    "job_skill": "Kubernetes",
                    "requirement_level": "Required",
                    "matched": False,
                    "severity_if_missing": "Blocking",
                },
                {
                    "job_skill": "Go",
                    "requirement_level": "Preferred",
                    "matched": False,
                    "severity_if_missing": "Minor",
                },
            ],
            "strengths": ["Solid Python"],
            "weaknesses": ["No container experience"],
            "recommendations": ["Learn Kubernetes"],
            "summary": "Partial fit.",
            **over,
        }
    )


def _gap_result() -> GapResult:
    return GapResult(
        overall_gap_score=45,
        strongest_area="Python",
        weakest_area="Infrastructure",
        gap_summary="Needs container and orchestration skills.",
        missing_skills=[
            SkillGapItem(
                skill="Docker",
                priority="Critical",
                importance_reason="Required by the role.",
                current_level="None",
                estimated_learning_time="1 month",
                prerequisite_skills=[],
                recommended_resources=["Docker Docs", "Play with Docker"],
                project_to_practice="Containerize an API",
                mandatory=True,
            )
        ],
    )


def _resume_result() -> ResumeResult:
    return ResumeResult(
        ats_score_before=51,
        ats_score_after=78,
        summary_of_changes=["Tightened bullets"],
        missing_information=["GitHub"],
        optimized_sections=[ResumeSection(title="Summary", content=["Engineer."])],
        final_resume_text="Nour Hassan\nEngineer",
    )


def _patch(monkeypatch, name: str, result=None, error=None):
    class _Chain:
        def invoke(self, _payload):
            if error:
                raise error
            return result

    monkeypatch.setattr(matching_service, name, lambda: _Chain())


# --- The spine: CV text comes from the profile, not the request ---


def test_match_requires_a_cv_on_the_profile(monkeypatch):
    db = _session()
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch, "build_job_match_chain", _match_result())

    with pytest.raises(NoCvOnProfile) as exc:
        matching_service.match_job(db, profile.id, JD)
    assert exc.value.status_code == 409


def test_missing_cv_is_checked_before_the_quota_is_charged(monkeypatch):
    """Never bill someone for a call that was never going to run."""
    db = _session()
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch, "build_job_match_chain", _match_result())

    with pytest.raises(NoCvOnProfile):
        matching_service.match_job(db, profile.id, JD)
    assert quota_service.usage_today(db, profile.id) == {}


def test_match_uses_the_profile_cv_text(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db, "UNIQUE-CV-MARKER")
    seen: dict = {}

    class _Chain:
        def invoke(self, payload):
            seen.update(payload)
            return _match_result()

    monkeypatch.setattr(matching_service, "build_job_match_chain", lambda: _Chain())
    matching_service.match_job(db, profile.id, JD)

    assert "UNIQUE-CV-MARKER" in seen["cv_text"]
    assert JD.strip() in seen["job_description"]


# --- Job match ---


def test_match_persists_seeds_skills_and_emits_an_event(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_job_match_chain", _match_result())

    record = matching_service.match_job(db, profile.id, JD, job_title="Backend Eng")

    assert record.match_score == 62
    assert record.job_title == "Backend Eng"
    assert db.query(JobMatch).count() == 1

    # Missing skills become unplanted seeds: present, but at zero mastery.
    seeds = {s.name: s for s in db.query(Skill).all()}
    assert seeds["Kubernetes"].mastery == 0
    assert seeds["Kubernetes"].source == "job_match"

    assert db.query(GrowthEvent).filter_by(type="job_matched").count() == 1


def test_seeding_never_demotes_a_skill_the_cv_proved(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    from app.schemas.profile import SkillIn

    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Kubernetes", mastery=70)], source="cv"
    )
    _patch(monkeypatch, "build_job_match_chain", _match_result())

    matching_service.match_job(db, profile.id, JD)

    kube = db.query(Skill).filter_by(name="Kubernetes").one()
    assert kube.mastery == 70


def test_matched_and_missing_never_overlap(monkeypatch):
    """The schema validator drops the contradiction; confirm it survives here."""
    db = _session()
    profile = _profile_with_cv(db)
    _patch(
        monkeypatch,
        "build_job_match_chain",
        _match_result(matched_skills=["Go"], missing_skills=["go", "Rust"]),
    )

    record = matching_service.match_job(db, profile.id, JD)
    matched = {s.lower() for s in record.result["matched_skills"]}
    missing = {s.lower() for s in record.result["missing_skills"]}
    assert not (matched & missing)


# --- Skill gap ---


def test_gap_persists_and_seeds(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_skill_gap_chain", _gap_result())

    record = matching_service.analyze_gap(db, profile.id, JD)

    assert record.overall_gap_score == 45
    assert db.query(SkillGapAnalysis).count() == 1
    assert db.query(Skill).filter_by(name="Docker").one().mastery == 0
    assert db.query(GrowthEvent).filter_by(type="gap_analyzed").count() == 1


# --- Resume optimizer ---


def test_resume_runs_without_a_job_description(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_resume_optimizer_chain", _resume_result())

    record = matching_service.optimize_resume(db, profile.id, job_description=None)

    assert record.ats_score_before == 51
    assert record.ats_score_after == 78
    assert record.job_description is None
    assert db.query(ResumeOptimization).count() == 1


def test_resume_emits_no_growth_event(monkeypatch):
    """Rewriting presentation is not skill growth. The farm must not claim it."""
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_resume_optimizer_chain", _resume_result())

    matching_service.optimize_resume(db, profile.id)
    assert db.query(GrowthEvent).count() == 0


# --- Failure and isolation ---


def test_chain_failure_becomes_a_clean_502(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(
        monkeypatch,
        "build_job_match_chain",
        error=RuntimeError("gemini refused: key sk-leaked"),
    )

    with pytest.raises(matching_service.AnalysisFailed) as exc:
        matching_service.match_job(db, profile.id, JD)

    assert "sk-leaked" not in exc.value.message
    assert exc.value.status_code == 502
    assert db.query(JobMatch).count() == 0


def test_quota_is_enforced_per_feature(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_job_match_chain", _match_result())
    _patch(monkeypatch, "build_skill_gap_chain", _gap_result())
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "job_match", 1)

    matching_service.match_job(db, profile.id, JD)
    with pytest.raises(QuotaExceeded):
        matching_service.match_job(db, profile.id, JD)

    # A different feature has its own budget.
    matching_service.analyze_gap(db, profile.id, JD)


def test_latest_is_scoped_to_the_caller(monkeypatch):
    db = _session()
    mine = _profile_with_cv(db)
    theirs = _profile_with_cv(db)
    _patch(monkeypatch, "build_job_match_chain", _match_result())

    matching_service.match_job(db, mine.id, JD)

    assert matching_service.latest_match(db, mine.id) is not None
    assert matching_service.latest_match(db, theirs.id) is None


# --- Cover letter ---


def _letter_result(**over) -> CoverLetterResult:
    return CoverLetterResult(
        **{
            "greeting": "Dear Hiring Team,",
            "opening": "I am applying for the Backend Engineer role.",
            "body": ["I built an API in Python.", "   ", ""],
            "closing": "I would welcome a conversation.",
            "sign_off": "Sincerely",
            "tone": "Formal",
            "evidence_used": ["Python engineer", "python engineer"],
            **over,
        }
    )


def test_blank_paragraphs_are_dropped():
    """The model pads the list. Empty paragraphs would render as gaps."""
    assert _letter_result().body == ["I built an API in Python."]


def test_full_text_assembles_the_whole_letter():
    """Assembled server-side so copy, download and any export cannot drift."""
    text = _letter_result().full_text

    assert text.startswith("Dear Hiring Team,")
    assert "I built an API in Python." in text
    assert text.endswith("Sincerely")


def test_full_text_is_not_requested_from_the_model():
    """It is computed. Asking the model to also write it invites the two to
    disagree, and the export would ship whichever one it happened to read."""
    assert "full_text" not in CoverLetterResult.model_json_schema()["properties"]


def test_cover_letter_persists_and_denormalises_the_text(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_cover_letter_chain", _letter_result())

    record = matching_service.write_cover_letter(
        db, profile.id, JD, job_title="Backend Eng"
    )

    assert record.job_title == "Backend Eng"
    assert record.full_text.startswith("Dear Hiring Team,")
    assert db.query(CoverLetterRecord).count() == 1


def test_a_letter_does_not_grow_the_farm(monkeypatch):
    """It presents capability the CV already proved. Nothing was learned, so
    no growth event and no seeded skills."""
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_cover_letter_chain", _letter_result())
    before = db.query(GrowthEvent).count()

    matching_service.write_cover_letter(db, profile.id, JD)

    assert db.query(GrowthEvent).count() == before
    assert db.query(Skill).count() == 0


def test_a_letter_needs_a_cv(monkeypatch):
    db = _session()
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch, "build_cover_letter_chain", _letter_result())

    with pytest.raises(NoCvOnProfile):
        matching_service.write_cover_letter(db, profile.id, JD)


def test_the_letter_quota_is_charged_before_the_chain(monkeypatch):
    db = _session()
    profile = _profile_with_cv(db)
    _patch(monkeypatch, "build_cover_letter_chain", _letter_result())

    matching_service.write_cover_letter(db, profile.id, JD)

    assert quota_service.usage_today(db, profile.id)["cover_letter"] == 1
