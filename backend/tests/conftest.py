import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
os.environ.setdefault("GOOGLE_API_KEY", "test")

import time
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.db import get_engine, get_sessionmaker
    from app.limiter import reset_rate_limit_state

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    reset_rate_limit_state()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    reset_rate_limit_state()


@pytest.fixture
def client():
    return TestClient(create_app())


def make_token(secret="test-secret", sub=None, email="a@b.com",
               exp_offset=3600, aud="authenticated"):
    # sub defaults to a fresh UUID: Supabase issues UUID subjects, and
    # profile_service.get_or_create parses it as one. A literal like
    # "user-123" would blow up there rather than in the auth layer.
    payload = {"sub": sub or str(uuid.uuid4()), "email": email, "aud": aud,
               "exp": int(time.time()) + exp_offset}
    return jwt.encode(payload, secret, algorithm="HS256")
