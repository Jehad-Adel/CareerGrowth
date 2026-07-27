from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.schemas.profile import ProfileOut, ProfileUpdate, SkillIn, SkillOut
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


class SkillsPayload(BaseModel):
    # Bounded deliberately: an unbounded list would let one request create
    # unbounded rows.
    skills: list[SkillIn] = Field(min_length=1, max_length=100)


@router.get("", response_model=ProfileOut)
def read_profile(profile: CurrentProfile) -> ProfileOut:
    return profile_service.to_out(profile)


@router.patch("", response_model=ProfileOut)
def patch_profile(
    patch: ProfileUpdate, profile: CurrentProfile, db: DbSession
) -> ProfileOut:
    updated = profile_service.update(db, profile.id, patch)
    return profile_service.to_out(updated)


@router.get("/skills", response_model=list[SkillOut])
def read_skills(profile: CurrentProfile) -> list[SkillOut]:
    return [SkillOut.model_validate(s) for s in profile.skills]


@router.post("/skills", response_model=list[SkillOut])
def add_skills(
    payload: SkillsPayload, profile: CurrentProfile, db: DbSession
) -> list[SkillOut]:
    skills = profile_service.upsert_skills(
        db, profile.id, payload.skills, source="manual"
    )
    return [SkillOut.model_validate(s) for s in skills]
