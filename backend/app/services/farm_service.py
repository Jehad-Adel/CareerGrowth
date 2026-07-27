"""The Farm: a read model over skills, goals, and the growth-event log.

This module writes nothing. Ever. The farm is a projection — if it ever became
its own source of truth it could drift from what the user actually did, which
is the exact failure the event log exists to prevent.
"""

import uuid
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import GrowthEvent, Roadmap, RoadmapStep, Skill
from app.services import xp_service

GrowthStage = Literal["seed", "sprout", "growing", "tree"]

# Mastery thresholds. A skill a job wants but the CV never proved sits at 0 and
# renders as an unplanted seed; one the CV evidenced starts as a sprout.
_STAGES: list[tuple[int, GrowthStage]] = [
    (75, "tree"),
    (50, "growing"),
    (1, "sprout"),
    (0, "seed"),
]

# How many events the farm's activity feed shows. Unbounded would grow forever
# and this endpoint is on the hot path for two pages.
FEED_LIMIT = 30


def stage_for(mastery: int) -> GrowthStage:
    for threshold, stage in _STAGES:
        if mastery >= threshold:
            return stage
    return "seed"


def plants(db: Session, profile_id: uuid.UUID) -> list[dict]:
    """Skills as plants, most grown first."""
    rows = db.execute(
        select(Skill)
        .where(Skill.profile_id == profile_id)
        .order_by(Skill.mastery.desc(), Skill.name)
    ).scalars()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "category": s.category,
            "mastery": s.mastery,
            "source": s.source,
            "stage": stage_for(s.mastery),
        }
        for s in rows
    ]


def feed(db: Session, profile_id: uuid.UUID, limit: int = FEED_LIMIT) -> list[dict]:
    """Most recent growth events. Bounded, newest first."""
    rows = db.execute(
        select(GrowthEvent)
        .where(GrowthEvent.profile_id == profile_id)
        .order_by(GrowthEvent.created_at.desc(), GrowthEvent.id.desc())
        .limit(limit)
    ).scalars()
    return [
        {
            "id": e.id,
            "type": e.type,
            "payload": e.payload,
            "xp": e.xp_awarded,
            "at": e.created_at.isoformat(),
        }
        for e in rows
    ]


def _step_progress(db: Session, profile_id: uuid.UUID) -> dict:
    """Roadmap completion, computed from the steps rather than stored."""
    roadmap = db.execute(
        select(Roadmap)
        .where(Roadmap.profile_id == profile_id)
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if roadmap is None:
        return {"has_roadmap": False, "target_role": None, "done": 0, "total": 0}

    total, done = db.execute(
        select(
            func.count(RoadmapStep.id),
            func.count(RoadmapStep.id).filter(RoadmapStep.status == "done"),
        ).where(RoadmapStep.roadmap_id == roadmap.id)
    ).one()

    return {
        "has_roadmap": True,
        "target_role": roadmap.target_role,
        "done": done or 0,
        "total": total or 0,
    }


def project(db: Session, profile_id: uuid.UUID, profile) -> dict:
    """The whole farm, in one read. Never writes."""
    level = xp_service.level_for_xp(profile.xp)
    grown = plants(db, profile_id)

    return {
        "level": level.level,
        "level_title": level.title,
        "xp": level.xp_in_level,
        "xp_for_next": level.xp_for_next,
        "streak_days": profile.streak_days,
        "plants": grown,
        "counts": {
            "total": len(grown),
            "seeds": sum(1 for p in grown if p["stage"] == "seed"),
            "trees": sum(1 for p in grown if p["stage"] == "tree"),
        },
        "roadmap": _step_progress(db, profile_id),
        "feed": feed(db, profile_id),
    }
