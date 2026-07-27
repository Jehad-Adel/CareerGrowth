import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.schemas.roadmap_schema import CareerRoadmap, RoadmapStep as StepResult
from app.auth import AuthUser
from app.db import Base
from app.errors import NoCvOnProfile, QuotaExceeded
from app.models import CareerProfile, GrowthEvent, Roadmap, RoadmapStep
from app.schemas.profile import ProfileUpdate, SkillIn
from app.services import (
    farm_service,
    profile_service,
    quota_service,
    roadmap_service,
    xp_service,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _ready_profile(db: Session) -> CareerProfile:
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    profile.cv_text = "Nour, Python engineer."
    db.commit()
    profile_service.update(db, profile.id, ProfileUpdate(target_role="Staff Engineer"))
    return profile


def _roadmap_result() -> CareerRoadmap:
    return CareerRoadmap(
        target_role="Staff Engineer",
        summary="Deepen systems and leadership.",
        steps=[
            StepResult(
                title="Learn Docker",
                description="Containerize an existing service.",
                skills_to_acquire=["Docker"],
                prerequisite_skills=[],
                estimated_duration_months=1,
            ),
            StepResult(
                title="Learn Kubernetes",
                description="Deploy that service to a cluster.",
                skills_to_acquire=["Kubernetes"],
                prerequisite_skills=["Docker"],
                estimated_duration_months=2,
            ),
        ],
        total_estimated_duration_months=3,
    )


def _patch(monkeypatch, result=None, error=None):
    class _Chain:
        def invoke(self, payload):
            if error:
                raise error
            _Chain.seen = payload
            return result or _roadmap_result()

    monkeypatch.setattr(roadmap_service, "build_roadmap_chain", lambda: _Chain())
    return _Chain


# --- Guards ---


def test_roadmap_requires_a_cv(monkeypatch):
    db = _session()
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch)
    with pytest.raises(NoCvOnProfile):
        roadmap_service.generate(db, profile.id)


def test_roadmap_requires_a_target_role(monkeypatch):
    db = _session()
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    profile.cv_text = "cv"
    db.commit()
    _patch(monkeypatch)

    with pytest.raises(roadmap_service.NoTargetRole) as exc:
        roadmap_service.generate(db, profile.id)
    assert exc.value.status_code == 409


def test_guards_run_before_the_quota_is_charged(monkeypatch):
    db = _session()
    profile = profile_service.get_or_create(
        db, AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    )
    _patch(monkeypatch)
    with pytest.raises(NoCvOnProfile):
        roadmap_service.generate(db, profile.id)
    assert quota_service.usage_today(db, profile.id) == {}


# --- Generation ---


def test_generate_plans_from_the_structured_profile_not_raw_cv(monkeypatch):
    """The chain must see current skills, including ones a job match found."""
    db = _session()
    profile = _ready_profile(db)
    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Python", mastery=60)], source="cv"
    )
    chain = _patch(monkeypatch)

    roadmap_service.generate(db, profile.id)

    sent = chain.seen["cv_profile"]
    assert sent["current_role"] is None or isinstance(sent["current_role"], str)
    assert {s["name"] for s in sent["skills"]} == {"Python"}
    assert chain.seen["target_role"] == "Staff Engineer"


def test_generate_persists_ordered_steps_and_an_event(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch)

    roadmap = roadmap_service.generate(db, profile.id)

    assert roadmap.target_role == "Staff Engineer"
    assert [s.position for s in roadmap.steps] == [0, 1]
    assert [s.title for s in roadmap.steps] == ["Learn Docker", "Learn Kubernetes"]
    assert all(s.status == "todo" for s in roadmap.steps)
    assert db.query(GrowthEvent).filter_by(type="roadmap_created").count() == 1


def test_generate_remembers_an_explicit_target_role(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch)

    roadmap_service.generate(db, profile.id, target_role="Principal Engineer")
    db.refresh(profile)
    assert profile.target_role in {"Principal Engineer", "Staff Engineer"}


def test_chain_failure_is_a_clean_502(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch, error=RuntimeError("gemini key sk-leak"))

    with pytest.raises(roadmap_service.AnalysisFailed) as exc:
        roadmap_service.generate(db, profile.id)
    assert "sk-leak" not in exc.value.message
    assert db.query(Roadmap).count() == 0


def test_roadmap_quota_is_enforced(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch)
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "roadmap", 1)

    roadmap_service.generate(db, profile.id)
    with pytest.raises(QuotaExceeded):
        roadmap_service.generate(db, profile.id)


# --- Completing a step: where the farm grows ---


def test_completing_a_step_awards_xp_and_emits_an_event(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch)
    roadmap = roadmap_service.generate(db, profile.id)
    before = profile.xp

    step = roadmap_service.complete_step(db, profile.id, roadmap.steps[0].id)

    assert step.status == "done"
    db.refresh(profile)
    assert profile.xp == before + xp_service.XP_AWARDS["goal_completed"]
    assert db.query(GrowthEvent).filter_by(type="goal_completed").count() == 1


def test_completing_a_step_twice_does_not_double_award(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch)
    roadmap = roadmap_service.generate(db, profile.id)

    roadmap_service.complete_step(db, profile.id, roadmap.steps[0].id)
    with pytest.raises(roadmap_service.StepAlreadyDone):
        roadmap_service.complete_step(db, profile.id, roadmap.steps[0].id)

    assert db.query(GrowthEvent).filter_by(type="goal_completed").count() == 1


def test_cannot_complete_another_users_step(monkeypatch):
    db = _session()
    mine = _ready_profile(db)
    theirs = _ready_profile(db)
    _patch(monkeypatch)
    roadmap = roadmap_service.generate(db, mine.id)

    # Indistinguishable from a step that does not exist.
    with pytest.raises(ValueError, match="No step"):
        roadmap_service.complete_step(db, theirs.id, roadmap.steps[0].id)


# --- Farm projection ---


def test_stage_thresholds():
    assert farm_service.stage_for(0) == "seed"
    assert farm_service.stage_for(1) == "sprout"
    assert farm_service.stage_for(49) == "sprout"
    assert farm_service.stage_for(50) == "growing"
    assert farm_service.stage_for(75) == "tree"
    assert farm_service.stage_for(100) == "tree"


def test_projection_writes_nothing(monkeypatch):
    """The farm is a read model. If it writes, it can drift from reality."""
    db = _session()
    profile = _ready_profile(db)
    _patch(monkeypatch)
    roadmap_service.generate(db, profile.id)

    before = (
        db.query(GrowthEvent).count(),
        db.query(RoadmapStep).count(),
        profile.xp,
    )
    farm_service.project(db, profile.id, profile)
    farm_service.project(db, profile.id, profile)
    db.refresh(profile)

    assert (
        db.query(GrowthEvent).count(),
        db.query(RoadmapStep).count(),
        profile.xp,
    ) == before


def test_projection_shape(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    profile_service.upsert_skills(
        db,
        profile.id,
        [SkillIn(name="Python", mastery=80), SkillIn(name="Rust", mastery=0)],
        source="cv",
    )
    _patch(monkeypatch)
    roadmap = roadmap_service.generate(db, profile.id)
    roadmap_service.complete_step(db, profile.id, roadmap.steps[0].id)

    farm = farm_service.project(db, profile.id, profile)

    stages = {p["name"]: p["stage"] for p in farm["plants"]}
    assert stages["Python"] == "tree"
    assert stages["Rust"] == "seed"
    assert farm["counts"]["trees"] == 1
    assert farm["counts"]["seeds"] == 1
    assert farm["roadmap"] == {
        "has_roadmap": True,
        "target_role": "Staff Engineer",
        "done": 1,
        "total": 2,
    }
    assert farm["feed"][0]["type"] == "goal_completed"  # newest first


def test_feed_is_bounded_and_scoped(monkeypatch):
    db = _session()
    mine = _ready_profile(db)
    theirs = _ready_profile(db)

    for i in range(40):
        xp_service.record_event(db, mine.id, "skill_discovered", {"n": i}, xp=0)

    assert len(farm_service.feed(db, mine.id)) == farm_service.FEED_LIMIT
    assert farm_service.feed(db, theirs.id) == []


def test_projection_with_no_roadmap(monkeypatch):
    db = _session()
    profile = _ready_profile(db)
    farm = farm_service.project(db, profile.id, profile)
    assert farm["roadmap"]["has_roadmap"] is False
    assert farm["plants"] == []
