import uuid
from io import BytesIO

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.loaders.pdf_loader import load_pdf_bytes
from app.ai.schemas.cv_profile import CVProfile, SeniorityLevel
from app.auth import AuthUser
from app.db import Base
from app.errors import QuotaExceeded
from app.models import CareerProfile, CvAnalysis, GrowthEvent, Skill
from app.services import cv_service, profile_service, quota_service

SAMPLE_PDF = "tests/ai/sample_data/cv.pdf"


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _profile(db: Session) -> CareerProfile:
    return profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )


def _fake_result() -> CVProfile:
    return CVProfile(
        full_name="Nour Hassan",
        current_role="Backend Engineer",
        years_of_experience=4,
        seniority_level=SeniorityLevel.MID,
        skills=["Python", "FastAPI", "python"],  # duplicate on purpose
        strengths=["Ships steadily"],
        weaknesses=["No metrics on impact"],
        summary="Backend engineer with four years of Python experience.",
        improvement_suggestions=["Quantify achievements"],
    )


def _patch_chain(monkeypatch, result=None, error=None):
    class _Chain:
        def invoke(self, _payload):
            if error:
                raise error
            return result or _fake_result()

    monkeypatch.setattr(cv_service, "build_cv_analysis_chain", lambda: _Chain())


# --- Upload validation (no AI involved) ---


def test_rejects_a_file_over_the_size_cap():
    with pytest.raises(cv_service.FileTooLarge):
        cv_service.validate_upload("cv.pdf", b"%PDF-" + b"x" * cv_service.MAX_UPLOAD_BYTES)


def test_rejects_an_empty_file():
    with pytest.raises(cv_service.UnsupportedFile):
        cv_service.validate_upload("cv.pdf", b"")


def test_rejects_a_non_pdf_even_with_a_pdf_filename():
    """A .docx renamed to .pdf must not get through. Content decides."""
    with pytest.raises(cv_service.UnsupportedFile):
        cv_service.validate_upload("cv.pdf", b"PK\x03\x04 this is a zip")


def test_accepts_a_real_pdf():
    with open(SAMPLE_PDF, "rb") as fh:
        cv_service.validate_upload("cv.pdf", fh.read())


# --- PDF loading ---


def test_load_pdf_bytes_extracts_text():
    with open(SAMPLE_PDF, "rb") as fh:
        text = load_pdf_bytes(BytesIO(fh.read()))
    assert len(text) > 100


def test_load_pdf_bytes_rejects_garbage():
    with pytest.raises(ValueError, match="not a readable PDF"):
        load_pdf_bytes(BytesIO(b"definitely not a pdf"))


def test_load_pdf_bytes_enforces_the_page_cap():
    with open(SAMPLE_PDF, "rb") as fh:
        with pytest.raises(ValueError, match="the limit is 0"):
            load_pdf_bytes(BytesIO(fh.read()), max_pages=0)


# --- analyze(): the spine ---


def test_analyze_writes_profile_skills_and_events(monkeypatch):
    db = _session()
    profile = _profile(db)
    _patch_chain(monkeypatch)

    with open(SAMPLE_PDF, "rb") as fh:
        analysis = cv_service.analyze(db, profile.id, "cv.pdf", fh.read())

    db.refresh(profile)
    assert profile.full_name == "Nour Hassan"
    assert profile.current_role == "Backend Engineer"
    assert profile.seniority_level == "Mid"
    assert profile.cv_text and len(profile.cv_text) > 100

    # "python" and "Python" are one plant.
    assert sorted(s.name for s in db.query(Skill).all()) == ["FastAPI", "Python"]
    assert db.query(CvAnalysis).count() == 1
    assert analysis.skills_found == 2

    types = {e.type for e in db.query(GrowthEvent).all()}
    assert types == {"cv_analyzed", "skill_discovered"}


def test_analyze_never_persists_the_uploaded_file(monkeypatch, tmp_path):
    """Parse-and-discard: the binary must not reach the filesystem or the DB."""
    db = _session()
    profile = _profile(db)
    _patch_chain(monkeypatch)

    with open(SAMPLE_PDF, "rb") as fh:
        raw = fh.read()
    cv_service.analyze(db, profile.id, "cv.pdf", raw)

    stored = db.query(CvAnalysis).one()
    assert "%PDF-" not in str(stored.result)
    db.refresh(profile)
    assert not profile.cv_text.startswith("%PDF-")


def test_analyze_charges_quota_and_stops_at_the_limit(monkeypatch):
    db = _session()
    profile = _profile(db)
    _patch_chain(monkeypatch)
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 1)

    with open(SAMPLE_PDF, "rb") as fh:
        raw = fh.read()

    cv_service.analyze(db, profile.id, "cv.pdf", raw)
    with pytest.raises(QuotaExceeded):
        cv_service.analyze(db, profile.id, "cv.pdf", raw)

    assert db.query(CvAnalysis).count() == 1


def test_a_chain_failure_does_not_leak_internals(monkeypatch):
    db = _session()
    profile = _profile(db)
    _patch_chain(monkeypatch, error=RuntimeError("gemini said: API key sk-secret"))

    with open(SAMPLE_PDF, "rb") as fh:
        with pytest.raises(cv_service.AnalysisFailed) as exc:
            cv_service.analyze(db, profile.id, "cv.pdf", fh.read())

    assert "sk-secret" not in exc.value.message
    assert "gemini" not in exc.value.message.lower()
    assert exc.value.status_code == 502
    assert db.query(CvAnalysis).count() == 0


def test_reanalysis_does_not_erase_user_edits(monkeypatch):
    """A thinner second CV must not wipe a target role the user set."""
    db = _session()
    profile = _profile(db)
    from app.schemas.profile import ProfileUpdate

    profile_service.update(db, profile.id, ProfileUpdate(target_role="Staff Engineer"))

    thin = _fake_result()
    thin.full_name = None
    thin.current_role = None
    _patch_chain(monkeypatch, result=thin)

    with open(SAMPLE_PDF, "rb") as fh:
        cv_service.analyze(db, profile.id, "cv.pdf", fh.read())

    db.refresh(profile)
    assert profile.target_role == "Staff Engineer"


def test_latest_returns_the_most_recent_and_is_scoped(monkeypatch):
    db = _session()
    mine = _profile(db)
    theirs = _profile(db)
    _patch_chain(monkeypatch)

    with open(SAMPLE_PDF, "rb") as fh:
        raw = fh.read()
    cv_service.analyze(db, mine.id, "cv.pdf", raw)

    assert cv_service.latest(db, mine.id) is not None
    assert cv_service.latest(db, theirs.id) is None
