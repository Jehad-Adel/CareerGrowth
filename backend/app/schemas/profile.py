import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=60)
    mastery: int = Field(default=0, ge=0, le=100)


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None
    mastery: int
    source: str


class ProfileUpdate(BaseModel):
    """Every field optional — this is a PATCH body."""

    full_name: str | None = Field(default=None, max_length=200)
    current_role: str | None = Field(default=None, max_length=200)
    target_role: str | None = Field(default=None, max_length=200)
    seniority_level: str | None = Field(default=None, max_length=20)
    summary: str | None = None


class ProfileOut(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None
    current_role: str | None
    target_role: str | None
    seniority_level: str | None
    summary: str | None
    # A boolean, not the text itself: cv_text runs to thousands of tokens and
    # the client never needs it.
    has_cv: bool
    level: int
    level_title: str
    # XP within the current level, not lifetime — the topbar renders
    # xp / xp_for_next as a progress bar.
    xp: int
    xp_for_next: int
    streak_days: int
    created_at: datetime
