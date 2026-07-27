import uuid
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import AiUsage, CareerProfile, Goal, GrowthEvent, Skill


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_profile_defaults_and_skill_cascade():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4(), email="a@b.com")
    db.add(profile)
    db.commit()

    assert profile.level == 1
    assert profile.xp == 0
    assert profile.streak_days == 0
    assert profile.created_at is not None

    db.add(Skill(profile_id=profile.id, name="Python", source="cv", mastery=40))
    db.commit()
    assert len(profile.skills) == 1

    db.delete(profile)
    db.commit()
    assert db.query(Skill).count() == 0


def test_growth_event_stores_json_payload():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    event = GrowthEvent(
        profile_id=profile.id,
        type="skill_discovered",
        payload={"skill": "Docker"},
        xp_awarded=10,
    )
    db.add(event)
    db.commit()
    assert db.query(GrowthEvent).one().payload == {"skill": "Docker"}


def test_goal_and_usage_defaults():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    goal = Goal(profile_id=profile.id, title="Learn Kubernetes")
    usage = AiUsage(profile_id=profile.id, day=date(2026, 7, 27), feature="cv_analysis")
    db.add_all([goal, usage])
    db.commit()

    assert goal.status == "active"
    assert goal.progress == 0
    assert usage.calls == 0
