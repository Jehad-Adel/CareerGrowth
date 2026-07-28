import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import matching_service

router = APIRouter(tags=["matching"])

# Bounds on free text that goes straight to a paid model. Too short is
# almost certainly a mistake; too long is a way to burn someone's quota
# and our token budget in one request.
MIN_JD = 50
MAX_JD = 20_000


class JobPayload(BaseModel):
    job_description: str = Field(min_length=MIN_JD, max_length=MAX_JD)
    job_title: str | None = Field(default=None, max_length=200)


class OptionalJobPayload(BaseModel):
    """The resume optimizer works with or without a target role."""

    job_description: str | None = Field(default=None, max_length=MAX_JD)
    job_title: str | None = Field(default=None, max_length=200)


class AnalysisOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    job_title: str | None
    result: dict


@router.post("/jobs/match", response_model=AnalysisOut)
@limiter.limit("10/minute")
def match_job(
    request: Request, payload: JobPayload, profile: CurrentProfile, db: DbSession
) -> AnalysisOut:
    record = matching_service.match_job(
        db, profile.id, payload.job_description, payload.job_title
    )
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.get("/jobs/latest", response_model=AnalysisOut | None)
def latest_match(profile: CurrentProfile, db: DbSession) -> AnalysisOut | None:
    record = matching_service.latest_match(db, profile.id)
    if record is None:
        return None
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.post("/skills/gap", response_model=AnalysisOut)
@limiter.limit("10/minute")
def analyze_gap(
    request: Request, payload: JobPayload, profile: CurrentProfile, db: DbSession
) -> AnalysisOut:
    record = matching_service.analyze_gap(
        db, profile.id, payload.job_description, payload.job_title
    )
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.get("/skills/gap/latest", response_model=AnalysisOut | None)
def latest_gap(profile: CurrentProfile, db: DbSession) -> AnalysisOut | None:
    record = matching_service.latest_gap(db, profile.id)
    if record is None:
        return None
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.post("/cv/optimize", response_model=AnalysisOut)
@limiter.limit("5/minute")
def optimize_resume(
    request: Request,
    payload: OptionalJobPayload,
    profile: CurrentProfile,
    db: DbSession,
) -> AnalysisOut:
    record = matching_service.optimize_resume(
        db, profile.id, payload.job_description, payload.job_title
    )
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.get("/cv/optimize/latest", response_model=AnalysisOut | None)
def latest_resume(profile: CurrentProfile, db: DbSession) -> AnalysisOut | None:
    record = matching_service.latest_resume(db, profile.id)
    if record is None:
        return None
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.post("/jobs/cover-letter", response_model=AnalysisOut)
@limiter.limit("5/minute")
def write_cover_letter(
    request: Request, payload: JobPayload, profile: CurrentProfile, db: DbSession
) -> AnalysisOut:
    record = matching_service.write_cover_letter(
        db, profile.id, payload.job_description, payload.job_title
    )
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )


@router.get("/jobs/cover-letter/latest", response_model=AnalysisOut | None)
def latest_cover_letter(profile: CurrentProfile, db: DbSession) -> AnalysisOut | None:
    record = matching_service.latest_cover_letter(db, profile.id)
    if record is None:
        return None
    return AnalysisOut(
        id=record.id,
        created_at=record.created_at,
        job_title=record.job_title,
        result=record.result,
    )
