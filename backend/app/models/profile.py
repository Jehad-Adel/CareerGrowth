import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class CareerProfile(UUIDPrimaryKey, Timestamps, Base):
    """The canonical record. Every feature reads and writes this."""

    __tablename__ = "career_profiles"

    # Supabase auth.users.id. Not a FK — that table lives in another schema.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320))

    full_name: Mapped[str | None] = mapped_column(String(200))
    current_role: Mapped[str | None] = mapped_column(String(200))
    target_role: Mapped[str | None] = mapped_column(String(200))
    years_of_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    seniority_level: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[str | None] = mapped_column(Text)

    # Parse-and-discard: the extracted text is kept, the uploaded file is not.
    #
    # Deferred because every authenticated request loads this profile, and this
    # column runs to thousands of tokens. Only the AI paths read the text; the
    # rest want `has_cv` below, which the database computes without shipping
    # the column. Touching `.cv_text` issues its own SELECT, by design.
    cv_text: Mapped[str | None] = mapped_column(Text, deferred=True)

    level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    xp: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    streak_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_active_on: Mapped[date | None] = mapped_column(Date)

    # Lazy, not selectin: `get_current_profile` runs on every authenticated
    # request, and selectin would issue two extra queries each time for
    # collections almost no endpoint reads. The farm and the skill upsert both
    # query these tables directly.
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


# Declared after the class so it can reference the mapped table column.
#
# The database answers "does this user have a CV?" in the SELECT that already
# loads the profile — no second query, and no shipping the CV text to find out
# it is non-empty. `length()` rather than `IS NOT NULL` because an empty string
# is not a CV.
CareerProfile.has_cv = column_property(
    func.coalesce(func.length(CareerProfile.__table__.c.cv_text), 0) > 0
)
