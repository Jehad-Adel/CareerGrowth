"""Records for the three job-oriented chains.

All three take the same input — the profile's CV text plus a job description —
so they change together and live together.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class _JobScoped(UUIDPrimaryKey, Timestamps):
    """Columns every job-description-driven analysis shares.

    `job_description` is nullable because the resume optimizer can run without
    a target role. The two chains that genuinely require it enforce that in
    their request schema, where required-ness belongs.
    """

    job_title: Mapped[str | None] = mapped_column(String(200))
    job_description: Mapped[str | None] = mapped_column(Text)
    # The chain's full structured output, verbatim: new fields render without
    # a migration, and a bad run stays diagnosable after the fact.
    result: Mapped[dict] = mapped_column(JSONType, nullable=False)


def _profile_fk() -> Mapped[uuid.UUID]:
    return mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class JobMatch(_JobScoped, Base):
    __tablename__ = "job_matches"

    profile_id: Mapped[uuid.UUID] = _profile_fk()
    # Denormalised so a history list sorts without unpacking JSON per row.
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)


class SkillGapAnalysis(_JobScoped, Base):
    __tablename__ = "skill_gap_analyses"

    profile_id: Mapped[uuid.UUID] = _profile_fk()
    overall_gap_score: Mapped[int] = mapped_column(Integer, nullable=False)


class ResumeOptimization(_JobScoped, Base):
    __tablename__ = "resume_optimizations"

    profile_id: Mapped[uuid.UUID] = _profile_fk()
    ats_score_before: Mapped[int] = mapped_column(Integer, nullable=False)
    ats_score_after: Mapped[int] = mapped_column(Integer, nullable=False)


class CoverLetter(_JobScoped, Base):
    """A letter written for one specific job from the profile's CV."""

    __tablename__ = "cover_letters"

    profile_id: Mapped[uuid.UUID] = _profile_fk()
    # Denormalised so a history list can show a preview without unpacking the
    # JSON, and so the export path never has to reassemble the letter.
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
