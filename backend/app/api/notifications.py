import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import CurrentProfile, DbSession
from app.services import notification_service

router = APIRouter(tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    body: str
    data: dict
    read: bool
    created_at: datetime


class UnreadCountOut(BaseModel):
    count: int


def _out(n) -> NotificationOut:
    return NotificationOut(
        id=str(n.id),
        type=n.type,
        title=n.title,
        body=n.body,
        data=dict(n.data),
        read=n.read,
        created_at=n.created_at,
    )


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(
    profile: CurrentProfile,
    db: DbSession,
) -> list[NotificationOut]:
    notification_service.check_deadlines(db, profile.id)
    return [_out(n) for n in notification_service.list_unread(db, profile.id)]


@router.get("/notifications/all", response_model=list[NotificationOut])
def list_all_notifications(
    profile: CurrentProfile,
    db: DbSession,
) -> list[NotificationOut]:
    return [_out(n) for n in notification_service.list_all(db, profile.id)]


@router.post("/notifications/{notification_id}/read", response_model=dict)
def read_notification(
    notification_id: uuid.UUID,
    profile: CurrentProfile,
    db: DbSession,
) -> dict:
    return {"read": notification_service.mark_read(db, profile.id, notification_id)}


@router.post("/notifications/read-all", response_model=dict)
def read_all_notifications(
    profile: CurrentProfile,
    db: DbSession,
) -> dict:
    return {"read": notification_service.mark_all_read(db, profile.id)}


@router.get("/notifications/count", response_model=UnreadCountOut)
def notification_count(
    profile: CurrentProfile,
    db: DbSession,
) -> UnreadCountOut:
    notification_service.check_deadlines(db, profile.id)
    return UnreadCountOut(count=notification_service.count_unread(db, profile.id))
