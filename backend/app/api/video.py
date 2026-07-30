import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import video_service

router = APIRouter(tags=["video"])


class VideoProcessIn(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
    mode: Literal["summary", "transcript"] = "summary"


class VideoSummaryOut(BaseModel):
    id: str
    url: str
    title: str
    source_type: str
    mode: str
    summary: str
    key_takeaways: list[str]
    transcript: str
    created_at: datetime


def _out(r) -> VideoSummaryOut:
    return VideoSummaryOut(
        id=str(r.id),
        url=r.url,
        title=r.title,
        source_type=r.source_type,
        mode=r.mode,
        summary=r.summary,
        key_takeaways=list(r.key_takeaways),
        transcript=r.transcript,
        created_at=r.created_at,
    )


@router.post("/video/process", response_model=VideoSummaryOut)
@limiter.limit("10/minute")
def process_video(
    request: Request,
    payload: VideoProcessIn,
    profile: CurrentProfile,
    db: DbSession,
) -> VideoSummaryOut:
    record = video_service.process(
        db, profile.id, url=payload.url, mode=payload.mode
    )
    return _out(record)


@router.get("/video/history", response_model=list[VideoSummaryOut])
def video_history(
    profile: CurrentProfile,
    db: DbSession,
) -> list[VideoSummaryOut]:
    return [_out(r) for r in video_service.history(db, profile.id)]


@router.get("/video/{video_id}", response_model=VideoSummaryOut)
def get_video(
    video_id: uuid.UUID,
    profile: CurrentProfile,
    db: DbSession,
) -> VideoSummaryOut:
    record = video_service.get(db, profile.id, video_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Video summary not found")
    return _out(record)
