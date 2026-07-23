from fastapi import APIRouter, Depends

from app.auth import AuthUser, get_current_user

router = APIRouter()


@router.get("/me", response_model=AuthUser)
def read_me(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user
