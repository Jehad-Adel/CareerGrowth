import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import offer_service

router = APIRouter(tags=["offers"])


class OfferEvalIn(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    offer_details: str = Field(min_length=20, max_length=20_000)


class OfferEvalOut(BaseModel):
    id: str
    company: str
    role_title: str
    overall_score: float | None
    recommendation: str
    result: dict
    created_at: datetime


def _out(r) -> OfferEvalOut:
    return OfferEvalOut(
        id=str(r.id),
        company=r.company,
        role_title=r.role_title,
        overall_score=r.overall_score,
        recommendation=r.recommendation,
        result=dict(r.result),
        created_at=r.created_at,
    )


@router.post("/offers/evaluate", response_model=OfferEvalOut)
@limiter.limit("5/minute")
def evaluate_offer(
    request: Request,
    payload: OfferEvalIn,
    profile: CurrentProfile,
    db: DbSession,
) -> OfferEvalOut:
    record = offer_service.evaluate(
        db,
        profile.id,
        company=payload.company,
        role_title=payload.role_title,
        offer_details=payload.offer_details,
    )
    return _out(record)


@router.get("/offers/latest", response_model=OfferEvalOut | None)
def latest_evaluation(
    profile: CurrentProfile,
    db: DbSession,
) -> OfferEvalOut | None:
    record = offer_service.latest(db, profile.id)
    return _out(record) if record else None


@router.get("/offers/history", response_model=list[OfferEvalOut])
def offer_history(
    profile: CurrentProfile,
    db: DbSession,
) -> list[OfferEvalOut]:
    return [_out(r) for r in offer_service.list_history(db, profile.id)]


@router.get("/offers/{offer_id}", response_model=OfferEvalOut)
def get_evaluation(
    offer_id: uuid.UUID,
    profile: CurrentProfile,
    db: DbSession,
) -> OfferEvalOut:
    record = offer_service.get(db, profile.id, offer_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return _out(record)
