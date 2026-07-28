import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy import Date, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey

# The pipeline, in order. Stored as a string rather than a native enum: adding
# a stage later is then a constant change here, not a migration that rewrites
# a type every replica is holding open.
STATUSES = ("saved", "applied", "interviewing", "offer", "rejected")

# Terminal states. `applied_at` stops meaning "waiting since" once reached.
CLOSED_STATUSES = frozenset({"offer", "rejected"})


class JobApplication(UUIDPrimaryKey, Timestamps, Base):
    """One role this person is actually pursuing.

    The rest of the app answers "should I apply?". This answers "what did I
    apply to, and what happened" — the part that brings someone back next week
    rather than once.

    Deliberately not derived from `job_matches`: plenty of applications are
    never scored first, and a tracker that only accepts analysed jobs would be
    a worse tracker. `job_match_id` is an optional link, not the source.
    """

    __tablename__ = "job_applications"
    __table_args__ = (
        Index("ix_job_applications_profile_status", "profile_id", "status"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="saved", server_default="saved"
    )
    # SET NULL, not CASCADE: deleting an old analysis must not delete the
    # record that you applied for the job.
    job_match_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("job_matches.id", ondelete="SET NULL"), index=True
    )
    applied_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    url: Mapped[str] = mapped_column(
        String(500), nullable=False, default="", server_default=""
    )
