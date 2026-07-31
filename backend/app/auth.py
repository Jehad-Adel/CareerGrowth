from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientError
from pydantic import BaseModel

from app.config import get_settings

bearer = HTTPBearer(auto_error=False)

# Supabase signs user access tokens with a rotating EC key and publishes the
# public half at this path. Locked to ES256 on purpose: accepting a list of
# algorithms is how JWT algorithm-confusion attacks get in, and a project on
# asymmetric signing keys never issues anything else.
_ALGORITHMS = ["ES256"]
_JWKS_PATH = "/auth/v1/.well-known/jwks.json"
# Supabase sets `iss` to <SUPABASE_URL>/auth/v1 on every access token.
_ISSUER_PATH = "/auth/v1"


class AuthUser(BaseModel):
    id: str
    email: str | None = None


@lru_cache
def _jwk_client() -> PyJWKClient:
    """Cached JWKS client. Fetches once, then serves keys from memory.

    PyJWKClient caches by `kid`, so Supabase rotating its signing key costs
    one extra fetch rather than breaking every request.
    """
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError(
            "SUPABASE_URL is not set. Copy .env.example to .env and fill it in."
        )
    return PyJWKClient(
        settings.supabase_url.rstrip("/") + _JWKS_PATH,
        cache_keys=True,
    )


def _issuer() -> str:
    """The `iss` value tokens from this project carry.

    Redundant with the JWKS pin -- a token from another Supabase project is
    signed by a key this project's JWKS never serves, so it fails on the
    signature first. Checked anyway because it is free, and because the pin
    is one config mistake away from pointing somewhere else.
    """
    return get_settings().supabase_url.rstrip("/") + _ISSUER_PATH


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthUser:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    try:
        signing_key = _jwk_client().get_signing_key_from_jwt(cred.credentials)
        payload = jwt.decode(
            cred.credentials,
            signing_key.key,
            algorithms=_ALGORITHMS,
            audience="authenticated",
            issuer=_issuer(),
            # PyJWT validates `exp` when it is present but does not insist it
            # is: a token minted without one would otherwise verify forever.
            # `sub` is required for the same reason -- it is the only thing
            # tying the token to a profile.
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except (jwt.PyJWTError, PyJWKClientError):
        # Never echo the underlying reason: it tells an attacker whether the
        # token was malformed, expired, or signed by the wrong key.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    return AuthUser(id=subject, email=payload.get("email"))
