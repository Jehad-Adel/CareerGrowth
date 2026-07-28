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
    reason: str
    difficulty: str
    skills_to_acquire: list[str]
    prerequisite_skills: list[str]
    recommended_resources: list[str]
    project_to_practice: str
    estimated_months: float
    estimated_weekly_hours: float
    status: str


def _step_out(step) -> StepOut:
    return StepOut(
        id=step.id,
        position=step.position,
        title=step.title,
        description=step.description,
        reason=step.reason,
        difficulty=step.difficulty,
        skills_to_acquire=list(step.skills_to_acquire),
        prerequisite_skills=list(step.prerequisite_skills),
        recommended_resources=list(step.recommended_resources),
        project_to_practice=step.project_to_practice,
        estimated_months=float(step.estimated_months),
        estimated_weekly_hours=float(step.estimated_weekly_hours),
        status=step.status,
    )


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
        steps=[_step_out(s) for s in roadmap.steps],
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


@router.get("/roadmap/history", response_model=list[RoadmapOut])
def roadmap_history(profile: CurrentProfile, db: DbSession) -> list[RoadmapOut]:
    return [_to_out(r) for r in roadmap_service.list_history(db, profile.id)]


@router.get("/roadmap/{roadmap_id}", response_model=RoadmapOut | None)
def read_roadmap(
    roadmap_id: uuid.UUID, profile: CurrentProfile, db: DbSession
) -> RoadmapOut | None:
    roadmap = roadmap_service.get(db, profile.id, roadmap_id)
    return _to_out(roadmap) if roadmap else None


@router.post("/roadmap/steps/{step_id}/complete", response_model=StepOut)
def complete_step(
    step_id: uuid.UUID, profile: CurrentProfile, db: DbSession
) -> StepOut:
    step = roadmap_service.complete_step(db, profile.id, step_id)
    return _step_out(step)


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
        "has_cv": profile.has_cv,
    }
