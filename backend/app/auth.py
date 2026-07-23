import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings

bearer = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    id: str
    email: str | None = None


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthUser:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    settings = get_settings()
    try:
        payload = jwt.decode(
            cred.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return AuthUser(id=payload["sub"], email=payload.get("email"))
