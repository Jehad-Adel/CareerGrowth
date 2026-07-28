import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.roadmap_chain import build_roadmap_chain
from app.errors import AppError, NoCvOnProfile
from app.logging import get_logger
from app.models import CareerProfile, Roadmap, RoadmapStep, Skill
from app.services import quota_service, rag_service, xp_service

log = get_logger(__name__)


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


class NoTargetRole(AppError):
    status_code = 409
    code = "no_target_role"


class StepAlreadyDone(AppError):
    status_code = 409
    code = "step_already_done"


def _profile_snapshot(db: Session, profile: CareerProfile) -> dict:
    """The structured profile the chain reads, not raw CV text.

    The roadmap prompt takes `cv_profile` as JSON precisely so it plans against
    what the profile knows now — including skills a job match discovered — and
    not against a stale copy of the CV.
    """
    skills = db.execute(
        select(Skill).where(Skill.profile_id == profile.id)
    ).scalars()
    return {
        "current_role": profile.current_role,
        "seniority_level": profile.seniority_level,
        "years_of_experience": (
            float(profile.years_of_experience)
            if profile.years_of_experience is not None
            else None
        ),
        "summary": profile.summary,
        "skills": [
            {"name": s.name, "mastery": s.mastery, "source": s.source}
            for s in skills
        ],
    }


def generate(
    db: Session, profile_id: uuid.UUID, target_role: str | None = None
) -> Roadmap:
    """Build a roadmap toward a target role.

    Falls back to the profile's stored target role so the common case needs no
    argument, and persists whichever one was used.
    """
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")
    if not profile.cv_text:
        raise NoCvOnProfile(
            "Analyze your CV first — a roadmap plans from where you actually are."
        )

    role = (target_role or profile.target_role or "").strip()
    if not role:
        raise NoTargetRole("Set a target role first, so there is somewhere to aim.")

    quota_service.consume(db, profile_id, "roadmap")

    try:
        result = build_roadmap_chain().invoke(
            {"cv_profile": _profile_snapshot(db, profile), "target_role": role}
        )
    except Exception as exc:
        log.exception("roadmap_chain_failed", profile_id=str(profile_id))
        raise AnalysisFailed(
            "The roadmap service could not build a plan. Try again shortly."
        ) from exc

    roadmap = Roadmap(
        profile_id=profile_id,
        target_role=result.target_role or role,
        summary=result.summary,
        total_estimated_months=result.total_estimated_duration_months,
        result=result.model_dump(mode="json"),
    )
    db.add(roadmap)
    db.flush()

    for index, step in enumerate(result.steps):
        db.add(
            RoadmapStep(
                roadmap_id=roadmap.id,
                profile_id=profile_id,
                position=index,
                title=step.title,
                description=step.description,
                reason=step.reason,
                difficulty=step.difficulty,
                skills_to_acquire=list(step.skills_to_acquire),
                prerequisite_skills=list(step.prerequisite_skills),
                recommended_resources=list(step.recommended_resources),
                project_to_practice=step.project_to_practice,
                estimated_months=step.estimated_duration_months,
                estimated_weekly_hours=step.estimated_weekly_hours,
            )
        )

    # Remember the role that was actually planned for.
    profile.target_role = roadmap.target_role

    xp_service.record_event(
        db,
        profile_id,
        "roadmap_created",
        {"roadmap_id": str(roadmap.id), "target_role": roadmap.target_role},
        xp=xp_service.XP_AWARDS["roadmap_created"],
    )

    # Best-effort corpus update: never lose a roadmap over a RAG failure.
    try:
        steps_text = "\n".join(
            f"{i + 1}. {s.title} ({s.estimated_duration_months} months, "
            f"{s.difficulty}): {s.description} {s.reason}".rstrip()
            for i, s in enumerate(result.steps)
        )
        rag_service.ingest(
            db,
            profile_id,
            "roadmap",
            f"Roadmap toward {roadmap.target_role}\n\n{roadmap.summary}\n\n{steps_text}",
            source_id=roadmap.id,
        )
    except Exception:
        log.exception("rag_ingest_failed", kind="roadmap", profile_id=str(profile_id))

    db.refresh(roadmap)
    return roadmap


def latest(db: Session, profile_id: uuid.UUID) -> Roadmap | None:
    return db.execute(
        select(Roadmap)
        .where(Roadmap.profile_id == profile_id)
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def complete_step(
    db: Session, profile_id: uuid.UUID, step_id: uuid.UUID
) -> RoadmapStep:
    """Mark a step done. This is the moment the farm actually grows.

    Scoped by profile_id in the WHERE clause, not checked after fetching: a
    step belonging to someone else must be indistinguishable from one that
    does not exist.
    """
    step = db.execute(
        select(RoadmapStep).where(
            RoadmapStep.id == step_id, RoadmapStep.profile_id == profile_id
        )
    ).scalar_one_or_none()
    if step is None:
        raise ValueError(f"No step {step_id}")
    if step.status == "done":
        # Idempotency matters: a double-click must not award XP twice.
        raise StepAlreadyDone("That step is already complete.")

    step.status = "done"
    db.flush()

    xp_service.record_event(
        db,
        profile_id,
        "goal_completed",
        {
            "step_id": str(step.id),
            "title": step.title,
            "skills": list(step.skills_to_acquire),
        },
        xp=xp_service.XP_AWARDS["goal_completed"],
    )

    db.refresh(step)
    return step
