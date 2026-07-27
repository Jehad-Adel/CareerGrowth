import uuid
from datetime import datetime

from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel

from app.deps import CurrentProfile, DbSession
from app.limiter import limiter
from app.services import cv_service, quota_service

router = APIRouter(prefix="/cv", tags=["cv"])


class CvAnalysisOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    skills_found: int
    # The raw CVProfile the chain produced. Rendered by the client; never
    # interpolated as HTML.
    result: dict


class CvStatusOut(BaseModel):
    has_cv: bool
    analyses_today: int
    daily_limit: int


@router.post("/analyze", response_model=CvAnalysisOut)
@limiter.limit("5/minute")
async def analyze_cv(
    request: Request,
    profile: CurrentProfile,
    db: DbSession,
    file: UploadFile = File(...),
) -> CvAnalysisOut:
    """Analyze an uploaded CV and write the results onto the profile.

    The file is read into memory, parsed, and discarded. Nothing is written to
    disk and no binary is persisted.

    `request` is unused in the body but required: slowapi's decorator resolves
    the client key from it.
    """
    # Read with a hard cap rather than trusting Content-Length, which lies.
    content = await file.read(cv_service.MAX_UPLOAD_BYTES + 1)
    cv_service.validate_upload(file.filename, content)

    analysis = cv_service.analyze(db, profile.id, file.filename, content)
    return CvAnalysisOut(
        id=analysis.id,
        created_at=analysis.created_at,
        skills_found=analysis.skills_found,
        result=analysis.result,
    )


@router.get("/latest", response_model=CvAnalysisOut | None)
def latest_analysis(profile: CurrentProfile, db: DbSession) -> CvAnalysisOut | None:
    analysis = cv_service.latest(db, profile.id)
    if analysis is None:
        return None
    return CvAnalysisOut(
        id=analysis.id,
        created_at=analysis.created_at,
        skills_found=analysis.skills_found,
        result=analysis.result,
    )


@router.get("/status", response_model=CvStatusOut)
def cv_status(profile: CurrentProfile, db: DbSession) -> CvStatusOut:
    """What the CV page needs to render before anything is uploaded."""
    used = quota_service.usage_today(db, profile.id)
    return CvStatusOut(
        has_cv=bool(profile.cv_text),
        analyses_today=used.get(cv_service.FEATURE, 0),
        daily_limit=quota_service.DAILY_LIMITS[cv_service.FEATURE],
    )
