import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import CareerProfile, GrowthEvent
from app.services import xp_service


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


@pytest.mark.parametrize(
    "xp,level,xp_in_level,xp_for_next",
    [
        (0, 1, 0, 100),
        (99, 1, 99, 100),
        (100, 2, 0, 150),
        (249, 2, 149, 150),
        (250, 3, 0, 200),
    ],
)
def test_level_curve(xp, level, xp_in_level, xp_for_next):
    info = xp_service.level_for_xp(xp)
    assert (info.level, info.xp_in_level, info.xp_for_next) == (
        level,
        xp_in_level,
        xp_for_next,
    )


def test_level_title_is_stable_and_capped():
    assert xp_service.level_for_xp(0).title == "Seedling"
    assert xp_service.level_for_xp(10_000_000).title == xp_service.LEVEL_TITLES[-1]


def test_record_event_appends_and_awards_xp():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    xp_service.record_event(
        db, profile.id, "cv_analyzed", {"analysis_id": "x"}, xp=50
    )
    xp_service.record_event(db, profile.id, "skill_discovered", {"skill": "Go"}, xp=10)

    db.refresh(profile)
    assert profile.xp == 60
    assert profile.level == 1
    assert db.query(GrowthEvent).count() == 2


def test_record_event_levels_the_profile_up():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    xp_service.record_event(db, profile.id, "cv_analyzed", {}, xp=120)
    db.refresh(profile)
    assert profile.level == 2


def test_record_event_rejects_an_unknown_profile():
    db = _session()
    with pytest.raises(ValueError, match="No profile"):
        xp_service.record_event(db, uuid.uuid4(), "cv_analyzed", {}, xp=10)
