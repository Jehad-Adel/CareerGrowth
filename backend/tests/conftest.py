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


def make_token(secret="test-secret", sub=None, email="a@b.com",
               exp_offset=3600, aud="authenticated"):
    # sub defaults to a fresh UUID: Supabase issues UUID subjects, and
    # profile_service.get_or_create parses it as one. A literal like
    # "user-123" would blow up there rather than in the auth layer.
    payload = {"sub": sub or str(uuid.uuid4()), "email": email, "aud": aud,
               "exp": int(time.time()) + exp_offset}
    return jwt.encode(payload, secret, algorithm="HS256")
