import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import farm_service, profile_service, roadmap_service, quota_service

router = APIRouter(tags=["roadmap"])


class RoadmapRequest(BaseModel):
    target_role: str | None = Field(default=None, max_length=200)


class StepOut(BaseModel):
    id: uuid.UUID
    position: int
    title: str
    description: str
    skills_to_acquire: list[str]
    prerequisite_skills: list[str]
    estimated_months: float
    status: str


class RoadmapOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    target_role: str
    summary: str
    total_estimated_months: float
    steps: list[StepOut]


def _to_out(roadmap) -> RoadmapOut:
    return RoadmapOut(
        id=roadmap.id,
        created_at=roadmap.created_at,
        target_role=roadmap.target_role,
        summary=roadmap.summary,
        total_estimated_months=float(roadmap.total_estimated_months),
        steps=[
            StepOut(
                id=s.id,
                position=s.position,
                title=s.title,
                description=s.description,
                skills_to_acquire=list(s.skills_to_acquire),
                prerequisite_skills=list(s.prerequisite_skills),
                estimated_months=float(s.estimated_months),
                status=s.status,
            )
            for s in roadmap.steps
        ],
    )


@router.post("/roadmap", response_model=RoadmapOut)
@limiter.limit("5/minute")
def generate_roadmap(
    request: Request,
    payload: RoadmapRequest,
    profile: CurrentProfile,
    db: DbSession,
) -> RoadmapOut:
    roadmap = roadmap_service.generate(db, profile.id, payload.target_role)
    return _to_out(roadmap)


@router.get("/roadmap", response_model=RoadmapOut | None)
def latest_roadmap(profile: CurrentProfile, db: DbSession) -> RoadmapOut | None:
    roadmap = roadmap_service.latest(db, profile.id)
    return _to_out(roadmap) if roadmap else None


@router.post("/roadmap/steps/{step_id}/complete", response_model=StepOut)
def complete_step(
    step_id: uuid.UUID, profile: CurrentProfile, db: DbSession
) -> StepOut:
    step = roadmap_service.complete_step(db, profile.id, step_id)
    return StepOut(
        id=step.id,
        position=step.position,
        title=step.title,
        description=step.description,
        skills_to_acquire=list(step.skills_to_acquire),
        prerequisite_skills=list(step.prerequisite_skills),
        estimated_months=float(step.estimated_months),
        status=step.status,
    )


@router.get("/farm")
def read_farm(profile: CurrentProfile, db: DbSession) -> dict:
    return farm_service.project(db, profile.id, profile)


@router.get("/dashboard")
def read_dashboard(profile: CurrentProfile, db: DbSession) -> dict:
    """Everything the dashboard needs, in one round trip.

    Five separate calls would each pay for auth, a JWKS check, and a
    connection checkout. This is the page's hot path.
    """
    return {
        "profile": profile_service.to_out(profile).model_dump(mode="json"),
        "farm": farm_service.project(db, profile.id, profile),
        "usage": quota_service.usage_today(db, profile.id),
        "has_cv": bool(profile.cv_text),
    }
