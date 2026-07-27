import os

# Pin the suite to a throwaway database before any app import. An OS env var
# takes precedence over the .env file in pydantic-settings, which is exactly
# what makes this work — and is also why GOOGLE_API_KEY must NOT be set here:
# doing so overrode the real key from .env and made every `-m live` test fail
# with "API key not valid". Unit tests patch the chain and never need a key.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "http://localhost")

import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

# Supabase signs access tokens with ES256 and publishes the public key at a
# JWKS endpoint. Tests mint their own P-256 keypair and stub the JWKS client,
# so the suite verifies real asymmetric signatures without a network call.
TEST_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
WRONG_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
TEST_KID = "test-signing-key"


class _StubSigningKey:
    def __init__(self, key):
        self.key = key


class _StubJWKClient:
    """Stands in for PyJWKClient, serving the test public key."""

    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, _token):
        return _StubSigningKey(self._public_key)


@pytest.fixture(autouse=True)
def _stub_jwks(monkeypatch):
    """Point auth at the test keypair instead of Supabase's JWKS endpoint."""
    import app.auth

    client = _StubJWKClient(TEST_SIGNING_KEY.public_key())
    monkeypatch.setattr(app.auth, "_jwk_client", lambda: client)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.auth import _jwk_client
    from app.db import get_engine, get_sessionmaker
    from app.limiter import reset_rate_limit_state

    def _clear():
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_sessionmaker.cache_clear()
        _jwk_client.cache_clear()
        reset_rate_limit_state()

    _clear()
    yield
    _clear()


@pytest.fixture
def client():
    """App wired to a throwaway in-memory database.

    StaticPool + check_same_thread=False because TestClient serves requests
    on a worker thread, and a fresh connection to :memory: would otherwise
    open an empty database with no schema.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool

    from app.db import Base, get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    db.close()


def make_token(key=None, sub=None, email="a@b.com", exp_offset=3600,
               aud="authenticated"):
    """Mint an ES256 token shaped like a Supabase access token.

    sub defaults to a fresh UUID because Supabase issues UUID subjects and
    profile_service.get_or_create parses it as one.
    """
    payload = {
        "sub": sub or str(uuid.uuid4()),
        "email": email,
        "aud": aud,
        "exp": int(time.time()) + exp_offset,
    }
    return jwt.encode(
        payload,
        key or TEST_SIGNING_KEY,
        algorithm="ES256",
        headers={"kid": TEST_KID},
    )
