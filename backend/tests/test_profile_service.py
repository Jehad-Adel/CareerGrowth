import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import AuthUser
from app.db import Base
from app.models import CareerProfile, GrowthEvent, Skill
from app.schemas.profile import ProfileUpdate, SkillIn
from app.services import profile_service


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _user(email="a@b.com") -> AuthUser:
    return AuthUser(id=str(uuid.uuid4()), email=email)


def test_get_or_create_is_idempotent():
    db = _session()
    user = _user()

    first = profile_service.get_or_create(db, user)
    second = profile_service.get_or_create(db, user)

    assert first.id == second.id
    assert first.email == "a@b.com"


def test_get_or_create_survives_a_concurrent_insert():
    """Two requests race to create the same profile; the loser must not 500.

    A page renders its layout and its content concurrently, so the very first
    authenticated call is usually several calls at once. All of them see no
    profile, all of them insert, and one loses on the unique index over
    user_id. This is the exact bug that made the first real login fail.
    """
    # One engine, two sessions -- otherwise each session gets its own
    # in-memory database and there is nothing to collide with.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)
    rival = Session(engine)

    user = _user()
    user_id = uuid.UUID(user.id)
    real_commit = db.commit
    calls = {"n": 0}

    def commit_losing_the_race():
        calls["n"] += 1
        if calls["n"] == 1:
            # The other request wins between our SELECT and our INSERT.
            rival.add(CareerProfile(user_id=user_id, email=user.email))
            rival.commit()
        return real_commit()

    db.commit = commit_losing_the_race  # type: ignore[method-assign]
    try:
        profile = profile_service.get_or_create(db, user)
    finally:
        db.commit = real_commit  # type: ignore[method-assign]

    assert profile.user_id == user_id
    assert db.query(CareerProfile).filter_by(user_id=user_id).count() == 1


def test_get_or_create_does_not_swallow_an_unrelated_integrity_error():
    """Only the race is recovered from; other violations must still surface."""
    db = _session()
    user = _user()

    def commit_that_always_fails():
        raise IntegrityError("INSERT", {}, Exception("something else broke"))

    db.commit = commit_that_always_fails  # type: ignore[method-assign]
    with pytest.raises(IntegrityError):
        profile_service.get_or_create(db, user)


def test_get_or_create_separates_users():
    db = _session()
    assert profile_service.get_or_create(db, _user()).id != (
        profile_service.get_or_create(db, _user("c@d.com")).id
    )


def test_update_applies_only_provided_fields():
    db = _session()
    user = _user()
    profile = profile_service.get_or_create(db, user)

    profile_service.update(db, profile.id, ProfileUpdate(target_role="Staff Engineer"))
    profile_service.update(db, profile.id, ProfileUpdate(full_name="Nour Hassan"))

    db.refresh(profile)
    assert profile.target_role == "Staff Engineer"
    assert profile.full_name == "Nour Hassan"


def test_update_can_clear_a_field_explicitly():
    """An explicit null must clear; an omitted key must not."""
    db = _session()
    profile = profile_service.get_or_create(db, _user())
    profile_service.update(db, profile.id, ProfileUpdate(summary="hello"))

    profile_service.update(
        db, profile.id, ProfileUpdate.model_validate({"summary": None})
    )
    db.refresh(profile)
    assert profile.summary is None


def test_update_rejects_an_unknown_profile():
    db = _session()
    with pytest.raises(ValueError, match="No profile"):
        profile_service.update(db, uuid.uuid4(), ProfileUpdate(full_name="x"))


def test_upsert_skills_dedupes_case_insensitively_and_emits_events():
    db = _session()
    user = _user()
    profile = profile_service.get_or_create(db, user)

    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Python"), SkillIn(name="Docker")], source="cv"
    )
    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="python"), SkillIn(name="Go")], source="cv"
    )

    names = sorted(s.name for s in profile_service.get_or_create(db, user).skills)
    assert names == ["Docker", "Go", "Python"]

    discovered = db.query(GrowthEvent).filter_by(type="skill_discovered").count()
    assert discovered == 3  # one per genuinely new skill, not per submission


def test_upsert_skills_raises_mastery_but_never_lowers_it():
    db = _session()
    profile = profile_service.get_or_create(db, _user())

    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Python", mastery=40)], source="cv"
    )
    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Python", mastery=70)], source="job_match"
    )
    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Python", mastery=10)], source="job_match"
    )

    skill = db.query(Skill).one()
    assert skill.mastery == 70
    assert db.query(GrowthEvent).filter_by(type="skill_leveled").count() == 1


def test_upsert_skills_ignores_blank_names():
    db = _session()
    profile = profile_service.get_or_create(db, _user())
    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="   "), SkillIn(name="Rust")], source="manual"
    )
    assert [s.name for s in db.query(Skill).all()] == ["Rust"]


def test_upsert_skills_dedupes_within_a_single_call():
    """The DB index is case-insensitive; two spellings in one payload must
    not attempt two inserts."""
    db = _session()
    profile = profile_service.get_or_create(db, _user())

    profile_service.upsert_skills(
        db,
        profile.id,
        [SkillIn(name="Kubernetes"), SkillIn(name="kubernetes")],
        source="cv",
    )
    assert db.query(Skill).count() == 1


def test_skill_names_are_case_insensitively_unique_in_the_database():
    """Guards the functional index itself, independent of the service."""
    db = _session()
    profile = profile_service.get_or_create(db, _user())
    db.add(Skill(profile_id=profile.id, name="Python", source="cv"))
    db.commit()
    db.add(Skill(profile_id=profile.id, name="python", source="cv"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_to_out_reports_xp_within_the_current_level():
    db = _session()
    profile = profile_service.get_or_create(db, _user())
    profile.xp = 120
    db.commit()

    out = profile_service.to_out(profile)
    assert out.level == 2
    assert out.xp == 20
    assert out.xp_for_next == 150
    assert out.level_title == "Sprout"


def test_to_out_reports_has_cv_without_exposing_the_text():
    db = _session()
    profile = profile_service.get_or_create(db, _user())
    assert profile_service.to_out(profile).has_cv is False

    profile.cv_text = "Nour Hassan, Senior Engineer..."
    db.commit()

    out = profile_service.to_out(profile)
    assert out.has_cv is True
    assert "cv_text" not in out.model_dump()
