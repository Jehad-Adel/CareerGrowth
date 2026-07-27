"""Job Match, Skill Gap, and Resume Optimizer.

One module rather than three near-identical ones: all three chains take the
same input (the profile's CV text plus a job description), run the same
guard/quota/invoke/persist sequence, and change together.

The CV text comes from the profile, never from the request. This is the spine
paying off — CV Studio already wrote it, so the user pastes only the job.
"""

import uuid
from typing import Callable, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.job_match_chain import build_job_match_chain
from app.ai.chains.resume_optimizer_chain import build_resume_optimizer_chain
from app.ai.chains.skill_gap_chain import build_skill_gap_chain
from app.errors import AppError, NoCvOnProfile
from app.logging import get_logger
from app.models import (
    CareerProfile,
    JobMatch,
    ResumeOptimization,
    SkillGapAnalysis,
)
from app.schemas.profile import SkillIn
from app.services import profile_service, quota_service, rag_service, xp_service

log = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# A skill the job wants but the CV does not evidence. Recorded at zero
# mastery so the farm can show it as an unplanted seed rather than a plant.
MISSING_SKILL_MASTERY = 0


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


def _require_cv(db: Session, profile_id: uuid.UUID) -> tuple[CareerProfile, str]:
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")
    if not profile.cv_text:
        # A typed 409, not a 500 — the client can act on this by sending the
        # user to CV Studio first.
        raise NoCvOnProfile(
            "Analyze your CV first — this reads the skills it already proved."
        )
    return profile, profile.cv_text


def _invoke(build: Callable[[], object], payload: dict, feature: str) -> BaseModel:
    """Run a chain, converting any provider failure into a clean 502."""
    try:
        return build().invoke(payload)  # type: ignore[attr-defined]
    except Exception as exc:
        log.exception("chain_failed", feature=feature)
        raise AnalysisFailed(
            "The analysis service could not process that. Try again shortly."
        ) from exc


def _ingest(
    db: Session, profile_id: uuid.UUID, kind: str, text: str, source_id: uuid.UUID
) -> None:
    """Add a result to the chat corpus. Best-effort: never lose a paid call."""
    try:
        rag_service.ingest(db, profile_id, kind, text, source_id=source_id)
    except Exception:
        log.exception("rag_ingest_failed", kind=kind, profile_id=str(profile_id))


def _seed_missing_skills(
    db: Session, profile_id: uuid.UUID, names: list[str], source: str
) -> None:
    """Record skills the job wants but the CV does not evidence.

    upsert_skills only ever raises mastery, so seeding at zero can never
    demote a skill the CV already established.
    """
    if not names:
        return
    profile_service.upsert_skills(
        db,
        profile_id,
        [SkillIn(name=name, mastery=MISSING_SKILL_MASTERY) for name in names],
        source=source,
    )


def match_job(
    db: Session,
    profile_id: uuid.UUID,
    job_description: str,
    job_title: str | None = None,
) -> JobMatch:
    _, cv_text = _require_cv(db, profile_id)
    quota_service.consume(db, profile_id, "job_match")

    result = _invoke(
        build_job_match_chain,
        {"cv_text": cv_text, "job_description": job_description},
        "job_match",
    )

    record = JobMatch(
        profile_id=profile_id,
        job_title=job_title,
        job_description=job_description,
        result=result.model_dump(mode="json"),
        match_score=result.match_score,  # type: ignore[attr-defined]
    )
    db.add(record)
    db.flush()

    _seed_missing_skills(
        db, profile_id, result.missing_skills, "job_match"  # type: ignore[attr-defined]
    )
    xp_service.record_event(
        db,
        profile_id,
        "job_matched",
        {"job_match_id": str(record.id), "score": record.match_score},
        xp=xp_service.XP_AWARDS["job_matched"],
    )
    _ingest(
        db,
        profile_id,
        "job_match",
        f"Job: {job_title or 'untitled'}\n\n{job_description}\n\n"
        f"Match summary: {result.summary}",  # type: ignore[attr-defined]
        record.id,
    )

    db.refresh(record)
    return record


def analyze_gap(
    db: Session,
    profile_id: uuid.UUID,
    job_description: str,
    job_title: str | None = None,
) -> SkillGapAnalysis:
    _, cv_text = _require_cv(db, profile_id)
    quota_service.consume(db, profile_id, "skill_gap")

    result = _invoke(
        build_skill_gap_chain,
        {"cv_text": cv_text, "job_description": job_description},
        "skill_gap",
    )

    record = SkillGapAnalysis(
        profile_id=profile_id,
        job_title=job_title,
        job_description=job_description,
        result=result.model_dump(mode="json"),
        overall_gap_score=result.overall_gap_score,  # type: ignore[attr-defined]
    )
    db.add(record)
    db.flush()

    _seed_missing_skills(
        db,
        profile_id,
        [item.skill for item in result.missing_skills],  # type: ignore[attr-defined]
        "skill_gap",
    )
    xp_service.record_event(
        db,
        profile_id,
        "gap_analyzed",
        {"analysis_id": str(record.id), "gap_score": record.overall_gap_score},
        xp=xp_service.XP_AWARDS["gap_analyzed"],
    )
    _ingest(
        db,
        profile_id,
        "skill_gap",
        f"Skill gap for: {job_title or 'untitled role'}\n\n"
        f"{result.gap_summary}",  # type: ignore[attr-defined]
        record.id,
    )

    db.refresh(record)
    return record


def optimize_resume(
    db: Session,
    profile_id: uuid.UUID,
    job_description: str | None = None,
    job_title: str | None = None,
) -> ResumeOptimization:
    """Rewrite the CV for ATS. The job description is optional here."""
    _, cv_text = _require_cv(db, profile_id)
    quota_service.consume(db, profile_id, "resume_optimizer")

    result = _invoke(
        build_resume_optimizer_chain,
        {"cv_text": cv_text, "job_description": job_description},
        "resume_optimizer",
    )

    record = ResumeOptimization(
        profile_id=profile_id,
        job_title=job_title,
        job_description=job_description,
        result=result.model_dump(mode="json"),
        ats_score_before=result.ats_score_before,  # type: ignore[attr-defined]
        ats_score_after=result.ats_score_after,  # type: ignore[attr-defined]
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # No growth event: this rewrites presentation, it does not add a skill,
    # and the farm must only reflect real capability.
    return record


def _latest(db: Session, model, profile_id: uuid.UUID):
    return db.execute(
        select(model)
        .where(model.profile_id == profile_id)
        .order_by(model.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def latest_match(db: Session, profile_id: uuid.UUID) -> JobMatch | None:
    return _latest(db, JobMatch, profile_id)


def latest_gap(db: Session, profile_id: uuid.UUID) -> SkillGapAnalysis | None:
    return _latest(db, SkillGapAnalysis, profile_id)


def latest_resume(db: Session, profile_id: uuid.UUID) -> ResumeOptimization | None:
    return _latest(db, ResumeOptimization, profile_id)
