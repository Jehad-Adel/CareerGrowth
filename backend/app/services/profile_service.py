import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import AuthUser
from app.models import CareerProfile, Skill
from app.schemas.profile import ProfileOut, ProfileUpdate, SkillIn
from app.services import xp_service


def get_or_create(db: Session, user: AuthUser) -> CareerProfile:
    """Fetch this user's profile, creating it on first sight.

    Signup happens entirely in Supabase, so the first authenticated API call
    is where the profile row comes into existence.
    """
    user_id = uuid.UUID(user.id)
    profile = db.execute(
        select(CareerProfile).where(CareerProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is not None:
        return profile

    profile = CareerProfile(user_id=user_id, email=user.email)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update(db: Session, profile_id: uuid.UUID, patch: ProfileUpdate) -> CareerProfile:
    """Apply a PATCH body. Omitted keys are left alone; explicit nulls clear."""
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")

    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def upsert_skills(
    db: Session, profile_id: uuid.UUID, skills: list[SkillIn], source: str
) -> list[Skill]:
    """Merge skills onto the profile, emitting one event per genuinely new one.

    Matching is case-insensitive so "python" from a job description does not
    plant a second tree next to "Python" from the CV. The database enforces
    the same rule via a functional unique index on (profile_id, lower(name)),
    so this is convenience, not the only line of defence.

    Mastery only ever rises. A job-match pass reporting a lower number than
    the CV already established must not demote the user's progress.
    """
    existing = {
        s.name.lower(): s
        for s in db.execute(
            select(Skill).where(Skill.profile_id == profile_id)
        ).scalars()
    }

    touched: list[Skill] = []
    for incoming in skills:
        key = incoming.name.strip().lower()
        if not key:
            continue

        current = existing.get(key)
        if current is None:
            current = Skill(
                profile_id=profile_id,
                name=incoming.name.strip(),
                category=incoming.category,
                mastery=incoming.mastery,
                source=source,
            )
            db.add(current)
            db.flush()
            # Register immediately so a duplicate spelling later in this same
            # payload resolves to this row instead of attempting a second
            # insert that the unique index would reject.
            existing[key] = current
            xp_service.record_event(
                db,
                profile_id,
                "skill_discovered",
                {"skill": current.name, "source": source},
                xp=xp_service.XP_AWARDS["skill_discovered"],
            )
        elif incoming.mastery > current.mastery:
            current.mastery = incoming.mastery
            xp_service.record_event(
                db,
                profile_id,
                "skill_leveled",
                {"skill": current.name, "mastery": current.mastery},
                xp=xp_service.XP_AWARDS["skill_leveled"],
            )
        touched.append(current)

    db.commit()
    return touched


def to_out(profile: CareerProfile) -> ProfileOut:
    """Project the model into the API shape, deriving level from total XP."""
    info = xp_service.level_for_xp(profile.xp)
    return ProfileOut(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        current_role=profile.current_role,
        target_role=profile.target_role,
        seniority_level=profile.seniority_level,
        summary=profile.summary,
        has_cv=bool(profile.cv_text),
        level=info.level,
        level_title=info.title,
        xp=info.xp_in_level,
        xp_for_next=info.xp_for_next,
        streak_days=profile.streak_days,
        created_at=profile.created_at,
    )
