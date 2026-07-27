from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import AuthUser, get_current_user
from app.db import get_db
from app.models import CareerProfile
from app.services import profile_service

DbSession = Annotated[Session, Depends(get_db)]


def get_current_profile(
    db: DbSession, user: Annotated[AuthUser, Depends(get_current_user)]
) -> CareerProfile:
    """Resolve the caller's profile, creating it on first authenticated call.

    Routes depend on this rather than accepting a profile_id from the client,
    so there is no request shape that lets one user address another's data.
    """
    return profile_service.get_or_create(db, user)


CurrentProfile = Annotated[CareerProfile, Depends(get_current_profile)]
