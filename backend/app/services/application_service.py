"""The application tracker.

No AI, no quota, no chain — the only service here that spends nothing. It is
plain CRUD, and the whole of its correctness is that every query filters on
`profile_id` in the WHERE clause rather than checking ownership after loading.
A row belonging to someone else must be indistinguishable from one that does
not exist.
"""

import uuid
from datetime import date, timezone, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.logging import get_logger
from app.models import JobApplication
from app.models.application import CLOSED_STATUSES, STATUSES

log = get_logger(__name__)

# Bounds a list endpoint the way the perf budget asks. Nobody is tracking more
# than this, and an unbounded query is how one account degrades the table.
PAGE_SIZE = 200


class UnknownStatus(AppError):
    status_code = 422
    code = "unknown_status"


def _validate(status: str) -> str:
    if status not in STATUSES:
        # Never echo the submitted value back into the message — it is
        # attacker-controlled text.
        raise UnknownStatus("That is not a stage in the pipeline.")
    return status


def create(
    db: Session,
    profile_id: uuid.UUID,
    *,
    company: str,
    role: str,
    status: str = "saved",
    job_match_id: uuid.UUID | None = None,
    url: str = "",
    notes: str = "",
) -> JobApplication:
    _validate(status)

    application = JobApplication(
        profile_id=profile_id,
        company=company.strip(),
        role=role.strip(),
        status=status,
        job_match_id=job_match_id,
        url=url.strip(),
        notes=notes.strip(),
        # Recording the date up front means the pipeline view can show "waiting
        # 12 days" without the user having to fill anything in.
        applied_at=_today() if status != "saved" else None,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def _today() -> date:
    return datetime.now(timezone.utc).date()


def list_for_profile(
    db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE
) -> list[JobApplication]:
    """Newest first. Grouping into columns is the UI's job, not a query."""
    return list(
        db.execute(
            select(JobApplication)
            .where(JobApplication.profile_id == profile_id)
            .order_by(JobApplication.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def set_status(
    db: Session, profile_id: uuid.UUID, application_id: uuid.UUID, status: str
) -> JobApplication:
    """Move one application along the pipeline.

    Scoped by profile_id in the WHERE clause, not checked after fetching.
    """
    _validate(status)
    application = db.execute(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.profile_id == profile_id,
        )
    ).scalar_one_or_none()
    if application is None:
        raise ValueError(f"No application {application_id}")

    # Stamp the date the first time it leaves "saved", and never overwrite it
    # afterwards — the question people ask is how long since they applied, not
    # since the last status change.
    if (
        application.applied_at is None
        and status != "saved"
        and status not in CLOSED_STATUSES
    ):
        application.applied_at = _today()

    application.status = status
    db.commit()
    db.refresh(application)
    return application


def update(
    db: Session,
    profile_id: uuid.UUID,
    application_id: uuid.UUID,
    *,
    notes: str | None = None,
    url: str | None = None,
) -> JobApplication:
    application = db.execute(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.profile_id == profile_id,
        )
    ).scalar_one_or_none()
    if application is None:
        raise ValueError(f"No application {application_id}")

    if notes is not None:
        application.notes = notes.strip()
    if url is not None:
        application.url = url.strip()

    db.commit()
    db.refresh(application)
    return application


def remove(db: Session, profile_id: uuid.UUID, application_id: uuid.UUID) -> bool:
    """Delete one. Returns whether anything was deleted.

    The profile_id predicate is what makes this safe: a DELETE by id alone
    would remove another user's row.
    """
    result = db.execute(
        delete(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.profile_id == profile_id,
        )
    )
    db.commit()
    return bool(result.rowcount)


def counts_by_status(db: Session, profile_id: uuid.UUID) -> dict[str, int]:
    """Every stage present, including the empty ones, so the UI renders a
    stable set of columns instead of a shifting one."""
    counts = dict.fromkeys(STATUSES, 0)
    for application in list_for_profile(db, profile_id):
        counts[application.status] = counts.get(application.status, 0) + 1
    return counts
