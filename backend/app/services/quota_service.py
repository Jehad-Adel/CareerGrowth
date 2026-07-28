import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import QuotaExceeded
from app.models import AiUsage

# Calls per user per UTC day. Tuned so a genuine user never notices and an
# abuser burns out fast. Raise deliberately, with the Gemini bill in view.
DAILY_LIMITS: dict[str, int] = {
    "cv_analysis": 10,
    "job_match": 20,
    "skill_gap": 20,
    "resume_optimizer": 10,
    "cover_letter": 10,
    "roadmap": 10,
    "interview_turn": 60,
    "chat_message": 100,
}


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _slot(db: Session, profile_id: uuid.UUID, feature: str, day: date) -> AiUsage:
    """Fetch today's counter row for this feature, creating it if absent.

    SELECT ... FOR UPDATE serialises concurrent callers on Postgres. SQLite
    ignores the clause, which is fine — the test suite is single-threaded.
    """
    stmt = (
        select(AiUsage)
        .where(
            AiUsage.profile_id == profile_id,
            AiUsage.day == day,
            AiUsage.feature == feature,
        )
        .with_for_update()
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is not None:
        return row

    row = AiUsage(profile_id=profile_id, day=day, feature=feature, calls=0)
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        # A concurrent request created the slot between our SELECT and INSERT.
        # Roll back the failed INSERT and read the row that won.
        db.rollback()
        row = db.execute(stmt).scalar_one()
    return row


def consume(db: Session, profile_id: uuid.UUID, feature: str) -> int:
    """Charge one AI call against today's budget. Returns the new count.

    Call this immediately *before* invoking a chain, never after — a failed
    generation still costs tokens.

    Raises:
        QuotaExceeded: today's budget for this feature is already spent.
        ValueError: the feature name is not a known AI feature.
    """
    limit = DAILY_LIMITS.get(feature)
    if limit is None:
        raise ValueError(f"Unknown AI feature: {feature!r}")

    day = _today()
    row = _slot(db, profile_id, feature, day)

    if row.calls >= limit:
        # Discard the pending read/insert so a rejected call never inflates
        # the counter — otherwise repeated rejections would push the number
        # ever further past the limit and corrupt usage reporting.
        db.rollback()
        raise QuotaExceeded(
            f"Daily limit for {feature} reached. Try again tomorrow.",
            feature=feature,
            limit=limit,
        )

    row.calls += 1
    db.commit()
    return row.calls


def usage_today(db: Session, profile_id: uuid.UUID) -> dict[str, int]:
    """Per-feature call counts for this profile so far today."""
    rows = db.execute(
        select(AiUsage.feature, AiUsage.calls).where(
            AiUsage.profile_id == profile_id, AiUsage.day == _today()
        )
    ).all()
    return {feature: calls for feature, calls in rows}
