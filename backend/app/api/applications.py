"""Application tracker routes. Validate, delegate, return."""

import uuid
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.models.application import STATUSES
from app.services import application_service

router = APIRouter(tags=["applications"])

Status = Literal["saved", "applied", "interviewing", "offer", "rejected"]


class ApplicationIn(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    status: Status = "saved"
    job_match_id: uuid.UUID | None = None
    url: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=5_000)


class StatusIn(BaseModel):
    status: Status


class ApplicationPatch(BaseModel):
    notes: str | None = Field(default=None, max_length=5_000)
    url: str | None = Field(default=None, max_length=500)


class ApplicationOut(BaseModel):
    id: uuid.UUID
    company: str
    role: str
    status: str
    job_match_id: uuid.UUID | None
    applied_at: date | None
    url: str
    notes: str
    created_at: datetime


class BoardOut(BaseModel):
    statuses: list[str]
    counts: dict[str, int]
    applications: list[ApplicationOut]


def _out(record) -> ApplicationOut:
    return ApplicationOut(
        id=record.id,
        company=record.company,
        role=record.role,
        status=record.status,
        job_match_id=record.job_match_id,
        applied_at=record.applied_at,
        url=record.url,
        notes=record.notes,
        created_at=record.created_at,
    )


@router.get("/applications", response_model=BoardOut)
def read_board(profile: CurrentProfile, db: DbSession) -> BoardOut:
    """The whole board in one call — the page renders every column at once."""
    records = application_service.list_for_profile(db, profile.id)
    return BoardOut(
        statuses=list(STATUSES),
        counts=application_service.counts_by_status(db, profile.id),
        applications=[_out(r) for r in records],
    )


@router.post("/applications", response_model=ApplicationOut)
@limiter.limit("30/minute")
def create_application(
    request: Request,
    payload: ApplicationIn,
    profile: CurrentProfile,
    db: DbSession,
) -> ApplicationOut:
    record = application_service.create(
        db,
        profile.id,
        company=payload.company,
        role=payload.role,
        status=payload.status,
        job_match_id=payload.job_match_id,
        url=payload.url,
        notes=payload.notes,
    )
    return _out(record)


@router.post("/applications/{application_id}/status", response_model=ApplicationOut)
def move_application(
    application_id: uuid.UUID,
    payload: StatusIn,
    profile: CurrentProfile,
    db: DbSession,
) -> ApplicationOut:
    record = application_service.set_status(
        db, profile.id, application_id, payload.status
    )
    return _out(record)


@router.patch("/applications/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: uuid.UUID,
    payload: ApplicationPatch,
    profile: CurrentProfile,
    db: DbSession,
) -> ApplicationOut:
    record = application_service.update(
        db, profile.id, application_id, notes=payload.notes, url=payload.url
    )
    return _out(record)


@router.delete("/applications/{application_id}")
def delete_application(
    application_id: uuid.UUID, profile: CurrentProfile, db: DbSession
) -> dict:
    return {"deleted": application_service.remove(db, profile.id, application_id)}
