"""The tracker. No AI, so the whole of its correctness is authorization.

Every method filters on `profile_id` in the WHERE clause. These tests exist
mostly to prove another profile's rows are unreachable — the failure mode here
is not a wrong answer, it is one user editing another's pipeline.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import AuthUser
from app.db import Base
from app.models import CareerProfile, JobApplication
from app.models.application import STATUSES
from app.services import application_service, profile_service


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _profile(db: Session) -> CareerProfile:
    return profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email=f"{uuid.uuid4().hex}@b.com")
    )


def _app(db: Session, profile, **over) -> JobApplication:
    return application_service.create(
        db,
        profile.id,
        **{"company": "Acme", "role": "Backend Engineer", **over},
    )


def test_a_saved_application_has_no_applied_date(db=None):
    db = _session()
    profile = _profile(db)

    record = _app(db, profile)

    assert record.status == "saved"
    assert record.applied_at is None


def test_creating_as_applied_stamps_the_date():
    db = _session()
    profile = _profile(db)

    record = _app(db, profile, status="applied")

    assert record.applied_at is not None


def test_moving_out_of_saved_stamps_the_date():
    db = _session()
    profile = _profile(db)
    record = _app(db, profile)

    moved = application_service.set_status(db, profile.id, record.id, "applied")

    assert moved.applied_at is not None


def test_the_applied_date_is_never_overwritten():
    """The question is how long since you applied, not since the last move."""
    db = _session()
    profile = _profile(db)
    record = _app(db, profile, status="applied")
    first = record.applied_at

    application_service.set_status(db, profile.id, record.id, "interviewing")
    moved = application_service.set_status(db, profile.id, record.id, "offer")

    assert moved.applied_at == first


def test_an_unknown_status_is_rejected():
    db = _session()
    profile = _profile(db)
    record = _app(db, profile)

    with pytest.raises(application_service.UnknownStatus) as exc:
        application_service.set_status(db, profile.id, record.id, "ghosted")
    assert exc.value.status_code == 422
    # The submitted value is attacker-controlled and must not be echoed back.
    assert "ghosted" not in exc.value.message


def test_listing_never_crosses_profiles():
    db = _session()
    mine, theirs = _profile(db), _profile(db)
    _app(db, mine, company="Mine")
    _app(db, theirs, company="Theirs")

    listed = application_service.list_for_profile(db, mine.id)

    assert [a.company for a in listed] == ["Mine"]


def test_another_profile_cannot_move_your_application():
    db = _session()
    mine, theirs = _profile(db), _profile(db)
    record = _app(db, mine)

    with pytest.raises(ValueError):
        application_service.set_status(db, theirs.id, record.id, "offer")

    assert db.get(JobApplication, record.id).status == "saved"


def test_another_profile_cannot_delete_your_application():
    db = _session()
    mine, theirs = _profile(db), _profile(db)
    record = _app(db, mine)

    assert application_service.remove(db, theirs.id, record.id) is False
    assert db.get(JobApplication, record.id) is not None

    assert application_service.remove(db, mine.id, record.id) is True
    assert db.get(JobApplication, record.id) is None


def test_another_profile_cannot_edit_your_notes():
    db = _session()
    mine, theirs = _profile(db), _profile(db)
    record = _app(db, mine, notes="mine")

    with pytest.raises(ValueError):
        application_service.update(db, theirs.id, record.id, notes="theirs")

    assert db.get(JobApplication, record.id).notes == "mine"


def test_counts_include_every_stage():
    """A stable set of columns, so the board does not reflow as it fills."""
    db = _session()
    profile = _profile(db)
    _app(db, profile)
    _app(db, profile, status="applied")

    counts = application_service.counts_by_status(db, profile.id)

    assert set(counts) == set(STATUSES)
    assert counts["saved"] == 1
    assert counts["applied"] == 1
    assert counts["offer"] == 0


def test_deleting_a_match_keeps_the_application():
    """ON DELETE SET NULL. Losing an old analysis must not erase the fact that
    you applied."""
    from app.models import JobMatch

    db = _session()
    profile = _profile(db)
    match = JobMatch(
        profile_id=profile.id, result={}, match_score=50, job_description="x"
    )
    db.add(match)
    db.commit()

    record = _app(db, profile, job_match_id=match.id)
    db.delete(match)
    db.commit()

    kept = db.get(JobApplication, record.id)
    assert kept is not None
    assert kept.job_match_id is None
