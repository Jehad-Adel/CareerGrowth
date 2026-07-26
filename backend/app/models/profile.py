import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    cv_text: Mapped[str | None] = mapped_column(Text)

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

    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
