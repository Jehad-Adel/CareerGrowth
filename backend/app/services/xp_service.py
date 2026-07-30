import uuid
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.logging import get_logger
from app.models import CareerProfile, GrowthEvent

log = get_logger(__name__)

LEVEL_TITLES = [
    "Seedling",
    "Sprout",
    "Sapling",
    "Grower",
    "Cultivator",
    "Gardener",
    "Orchardist",
    "Harvester",
    "Farmstead",
    "Homesteader",
]

# XP required for level 2 is _BASE; each subsequent level costs _STEP more.
_BASE = 100
_STEP = 50

XP_AWARDS = {
    "cv_analyzed": 50,
    "skill_discovered": 10,
    "skill_leveled": 15,
    "job_matched": 20,
    "gap_analyzed": 20,
    "roadmap_created": 40,
    "goal_completed": 60,
    "interview_completed": 75,
    "quiz_completed": 30,
    "video_summarized": 15,
    "video_transcribed": 5,
    "applied_job": 25,
    "cv_optimized": 20,
    "offer_evaluated": 35,
    "daily_login": 5,
}


class LevelInfo(NamedTuple):
    level: int
    title: str
    xp_in_level: int
    xp_for_next: int


def level_for_xp(xp: int) -> LevelInfo:
    """Map total lifetime XP to a level and progress within that level."""
    level = 1
    remaining = max(xp, 0)
    cost = _BASE
    while remaining >= cost:
        remaining -= cost
        level += 1
        cost += _STEP
    title = LEVEL_TITLES[min(level - 1, len(LEVEL_TITLES) - 1)]
    return LevelInfo(level=level, title=title, xp_in_level=remaining, xp_for_next=cost)


def record_event(
    db: Session,
    profile_id: uuid.UUID,
    type: str,
    payload: dict,
    xp: int = 0,
) -> GrowthEvent:
    """Append a growth event and re-derive the profile's level from total XP.

    The event log is the source of truth; profile.xp and profile.level are a
    denormalised cache so the topbar does not aggregate on every render.

    The profile is resolved before the event is added, so a bad profile_id
    leaves nothing pending in the session.
    """
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")

    event = GrowthEvent(
        profile_id=profile_id, type=type, payload=payload or {}, xp_awarded=xp
    )
    db.add(event)

    profile.xp += xp
    profile.level = level_for_xp(profile.xp).level

    # Update streak on any XP-earning engagement
    try:
        from app.services.streak_service import record_activity
        record_activity(db, profile_id)
    except Exception:
        log.exception("streak_update_failed", profile_id=str(profile_id))

    db.commit()
    db.refresh(event)
    return event
