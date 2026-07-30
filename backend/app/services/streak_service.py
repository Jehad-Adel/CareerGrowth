import uuid
from datetime import date, datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.logging import get_logger
from app.models import CareerProfile
from app.services import xp_service

log = get_logger(__name__)


def record_activity(db: Session, profile_id: uuid.UUID) -> None:
    """Update streak days and last_active_on for a profile.

    Called on any meaningful user engagement.
    - If last_active_on was yesterday: increment streak_days
    - If last_active_on is today: no change (idempotent)
    - If last_active_on is older (or None): reset streak_days to 1
    """
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")

    today = datetime.now(timezone.utc).date()

    if profile.last_active_on == today:
        return

    if profile.last_active_on == today - timedelta(days=1):
        profile.streak_days += 1
    else:
        profile.streak_days = 1

    profile.last_active_on = today

    # Award daily login XP when streak is maintained
    if profile.streak_days == 1 or (
        profile.last_active_on and profile.last_active_on == today
    ):
        pass

    db.flush()


def get_streak_info(db: Session, profile_id: uuid.UUID) -> dict:
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")
    return {
        "streak_days": profile.streak_days,
        "last_active_on": profile.last_active_on,
    }
