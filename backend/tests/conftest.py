import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "test")

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    return TestClient(create_app())


def make_token(secret="test-secret", sub="user-123", email="a@b.com",
               exp_offset=3600, aud="authenticated"):
    payload = {"sub": sub, "email": email, "aud": aud,
               "exp": int(time.time()) + exp_offset}
    return jwt.encode(payload, secret, algorithm="HS256")
