import uuid

from sqlalchemy import ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import JSONType, Timestamps, UUIDPrimaryKey


class CvAnalysis(UUIDPrimaryKey, Timestamps, Base):
    """One stored CV Analysis run.

    `result` is the full CVProfile the chain returned, kept verbatim so the
    UI can render new fields without a migration and so a bad extraction can
    be diagnosed after the fact. The extracted CV *text* lives on the profile
    (`career_profiles.cv_text`), not here — one copy, not two.
    """

    __tablename__ = "cv_analyses"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    result: Mapped[dict] = mapped_column(JSONType, nullable=False)
    # Denormalised for cheap list/sort without unpacking JSON on every row.
    skills_found: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
