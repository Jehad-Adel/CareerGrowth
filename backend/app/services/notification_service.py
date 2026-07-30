import uuid
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.logging import get_logger
from app.models import JobApplication, Notification

log = get_logger(__name__)

PAGE_SIZE = 100


def create(
    db: Session,
    profile_id: uuid.UUID,
    *,
    type: str,
    title: str,
    body: str = "",
    data: dict | None = None,
) -> Notification:
    notification = Notification(
        profile_id=profile_id,
        type=type,
        title=title,
        body=body,
        data=data or {},
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_unread(db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE) -> list[Notification]:
    return list(
        db.execute(
            select(Notification)
            .where(Notification.profile_id == profile_id, Notification.read == False)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def list_all(db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE) -> list[Notification]:
    return list(
        db.execute(
            select(Notification)
            .where(Notification.profile_id == profile_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def mark_read(db: Session, profile_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
    result = db.execute(
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.profile_id == profile_id,
        )
        .values(read=True)
    )
    db.commit()
    return bool(result.rowcount)


def mark_all_read(db: Session, profile_id: uuid.UUID) -> int:
    result = db.execute(
        update(Notification)
        .where(
            Notification.profile_id == profile_id,
            Notification.read == False,
        )
        .values(read=True)
    )
    db.commit()
    return result.rowcount


def count_unread(db: Session, profile_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count(Notification.id)).where(
            Notification.profile_id == profile_id,
            Notification.read == False,
        )
    ).scalar_one()


def check_deadlines(db: Session, profile_id: uuid.UUID) -> list[Notification]:
    """Check for approaching deadlines and create notifications if needed."""
    today = datetime.now(timezone.utc).date()
    warning_date = today + timedelta(days=3)

    upcoming = list(
        db.execute(
            select(JobApplication).where(
                JobApplication.profile_id == profile_id,
                JobApplication.deadline_at.is_not(None),
                JobApplication.deadline_at <= warning_date,
                JobApplication.deadline_at >= today,
                JobApplication.notified_deadline == False,
            )
        ).scalars()
    )

    created: list[Notification] = []
    for app in upcoming:
        days_left = (app.deadline_at - today).days
        if days_left < 0:
            continue
        notification = create(
            db,
            profile_id,
            type="deadline_approaching",
            title=f"Deadline approaching: {app.role} at {app.company}",
            body=(
                f"Application deadline for {app.role} at {app.company} "
                f"is in {days_left} day{'s' if days_left != 1 else ''} "
                f"({app.deadline_at})."
            ),
            data={
                "application_id": str(app.id),
                "deadline": str(app.deadline_at),
                "days_left": days_left,
            },
        )
        app.notified_deadline = True
        created.append(notification)

    if created:
        db.commit()

    return created
