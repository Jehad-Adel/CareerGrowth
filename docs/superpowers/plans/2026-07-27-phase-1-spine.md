# Phase 1 — Spine: schema, profile, quota, hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give CareerFarm a real database, a canonical `CareerProfile`, an append-only growth-event log, an AI usage quota, and the security/observability baseline every later phase builds on.

**Architecture:** SQLAlchemy 2 declarative models under `app/models/`, Alembic migrations, a thin service layer under `app/services/` that owns all authorization by filtering on `profile_id`, and FastAPI routers that do nothing but validate input and delegate. Cross-cutting concerns (request id, structured logging, error taxonomy, security headers, rate limiting) are installed once in `app/main.py`.

**Tech Stack:** FastAPI · Python 3.11 · uv · SQLAlchemy 2 (sync) · Alembic · Supabase Postgres · structlog · slowapi · pytest

## Global Constraints

Inherited from [the roadmap](2026-07-27-ship-roadmap.md#global-constraints). Repeated here because you may be reading this file alone:

- Python `>=3.11`, managed with `uv`. Never `pip install` into `backend/`.
- No LangChain import outside `backend/app/ai/` (that directory does not exist yet — Phase 3 creates it).
- Every service method that reads user data takes `profile_id` and filters on it. Authorization is the service layer's job, not the route's and not RLS's.
- Every new table gets `ENABLE ROW LEVEL SECURITY` with **no permissive policy**. Deny-by-default. The backend role bypasses RLS; this exists solely so a leaked browser `anon` key reads nothing.
- Never return `str(exception)` or a traceback to the client.
- Sync SQLAlchemy only. No `async def` on anything touching a DB session.
- Run tests from `backend/`: `uv run pytest -q`. Expected baseline before you start: `10 passed`.
- Commit after every green cycle. Conventional Commits.

**Working directory for every command in this plan is `backend/` unless stated otherwise.**

---

### Task 1: Dependencies and settings

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Settings.environment: str`, `Settings.debug: bool`, `Settings.is_production: bool`. Every later task reads these.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_config.py`:

```python
def test_environment_defaults_to_development(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    s = get_settings()
    assert s.environment == "development"
    assert s.is_production is False


def test_is_production_when_environment_is_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    s = get_settings()
    assert s.is_production is True


def test_cors_origin_list_strips_blanks_and_slashes(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com/, ,https://b.com")
    assert get_settings().cors_origin_list == ["https://a.com", "https://b.com"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -q`
Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'environment'`

- [ ] **Step 3: Add the dependencies**

```bash
uv add "structlog>=24.4" "slowapi>=0.1.9" "sentry-sdk[fastapi]>=2.18" "pgvector>=0.3"
```

`pgvector` is added now, not in Phase 7, so `0002_core_schema` and every later migration share one dependency set and `uv.lock` does not churn.

- [ ] **Step 4: Add the settings fields**

In `backend/app/config.py`, inside `class Settings`, after `cors_origins`:

```python
    environment: str = "development"
    debug: bool = False
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `13 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/config.py backend/tests/test_config.py
git commit -m "feat(config): add environment, debug, and sentry settings"
```

---

### Task 2: Lazy engine with production pool sizing

Today `app/db.py:6` calls `create_engine(get_settings().database_url)` at **module import**. With `DATABASE_URL` unset that is `create_engine("")`, which raises `ArgumentError` and takes down the whole process on import. It only survives today because `main.py` never imports `app.db`. Phase 1 makes `main.py` import it, so this must be fixed first.

**Files:**
- Modify: `backend/app/db.py`
- Test: `backend/tests/test_db.py`

**Interfaces:**
- Consumes: `Settings.database_url` (Task 1).
- Produces: `Base`, `get_engine() -> Engine`, `get_sessionmaker() -> sessionmaker[Session]`, `get_db() -> Iterator[Session]`. `SessionLocal` is removed; nothing outside `db.py` referenced it.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_db.py`:

```python
import pytest

from app.config import get_settings
from app.db import get_engine


def test_engine_raises_clear_error_when_database_url_missing(monkeypatch):
    get_settings.cache_clear()
    get_engine.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        get_engine()
    get_settings.cache_clear()
    get_engine.cache_clear()


def test_engine_skips_pool_sizing_for_sqlite(monkeypatch):
    get_settings.cache_clear()
    get_engine.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    engine = get_engine()
    assert engine.dialect.name == "sqlite"
    get_settings.cache_clear()
    get_engine.cache_clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py -q`
Expected: FAIL with `ImportError: cannot import name 'get_engine' from 'app.db'`

- [ ] **Step 3: Rewrite `backend/app/db.py`**

```python
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

Base = declarative_base()


@lru_cache
def get_engine() -> Engine:
    """Build the process-wide engine on first use, not at import time."""
    url = get_settings().database_url
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
        )

    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if not url.startswith("sqlite"):
        # Sized for the Supabase transaction pooler. SQLite's pool
        # implementations reject these arguments, hence the guard.
        kwargs.update(pool_size=5, max_overflow=5, pool_recycle=300)

    return create_engine(url, **kwargs)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Clear the engine cache between tests**

In `backend/tests/conftest.py`, extend the existing autouse fixture:

```python
@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.db import get_engine, get_sessionmaker

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
```

The import sits inside the fixture body so importing `conftest` never triggers engine construction.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `15 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/app/db.py backend/tests/test_db.py backend/tests/conftest.py
git commit -m "fix(db): build engine lazily and size the pool for the Supabase pooler"
```

---

### Task 3: Structured logging, request ids, and an error taxonomy

The current blanket handler at `app/main.py:23` returns `{"detail": "Internal server error"}` and **logs nothing**. Every production 500 is currently invisible.

**Files:**
- Create: `backend/app/logging.py`
- Create: `backend/app/errors.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_errors.py`

**Interfaces:**
- Consumes: `Settings.debug` (Task 1).
- Produces:
  - `configure_logging(debug: bool) -> None`
  - `request_id_var: ContextVar[str]`, `new_request_id() -> str`
  - `class AppError(Exception)` with `status_code: int`, `code: str`, `message: str`, `extra: dict`
  - `class QuotaExceeded(AppError)` — 429, `code="quota_exceeded"`
  - `class NoCvOnProfile(AppError)` — 409, `code="no_cv_on_profile"`
  - `install_error_handlers(app: FastAPI) -> None`

  Tasks 8 and later raise these. Phase 4 raises `NoCvOnProfile`.

- [ ] **Step 1: Write the failing test**

Replace `backend/tests/test_errors.py` with:

```python
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.errors import AppError, QuotaExceeded
from app.main import create_app


def _client_with(route_fn, path="/boom"):
    app = create_app()
    router = APIRouter()
    router.add_api_route(path, route_fn, methods=["GET"])
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_error_returns_500_json_with_request_id():
    def boom():
        raise RuntimeError("kaboom")

    r = _client_with(boom).get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"]
    assert "kaboom" not in r.text  # never leak the message


def test_app_error_maps_to_its_status_and_code():
    def boom():
        raise QuotaExceeded("Daily limit reached", feature="cv_analysis", limit=10)

    r = _client_with(boom).get("/boom")
    assert r.status_code == 429
    body = r.json()
    assert body["code"] == "quota_exceeded"
    assert body["detail"] == "Daily limit reached"
    assert body["feature"] == "cv_analysis"
    assert body["limit"] == 10


def test_request_id_echoed_in_header():
    def ok():
        return {"ok": True}

    r = _client_with(ok, path="/ok").get("/ok", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"


def test_base_app_error_defaults():
    err = AppError("nope")
    assert err.status_code == 400
    assert err.code == "app_error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_errors.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.errors'`

- [ ] **Step 3: Create `backend/app/logging.py`**

```python
import logging
import sys
import uuid
from contextvars import ContextVar

import structlog

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def _add_request_id(_logger, _method_name, event_dict: dict) -> dict:
    event_dict["request_id"] = request_id_var.get()
    return event_dict


def configure_logging(debug: bool = False) -> None:
    """JSON logs in production, human-readable locally. Idempotent."""
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
            if debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
```

- [ ] **Step 4: Create `backend/app/errors.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logging import get_logger, request_id_var

log = get_logger(__name__)


class AppError(Exception):
    """Base for expected, client-facing failures. Never leaks internals."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, **extra) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra


class QuotaExceeded(AppError):
    status_code = 429
    code = "quota_exceeded"


class NoCvOnProfile(AppError):
    status_code = 409
    code = "no_cv_on_profile"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        log.warning(
            "app_error",
            code=exc.code,
            path=request.url.path,
            method=request.method,
            **exc.extra,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "request_id": request_id_var.get(),
                **exc.extra,
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception(
            "unhandled_exception", path=request.url.path, method=request.method
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "code": "internal_error",
                "request_id": request_id_var.get(),
            },
        )
```

- [ ] **Step 5: Wire it into `backend/app/main.py`**

Replace the whole file:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api import health, me
from app.config import get_settings
from app.errors import install_error_handlers
from app.logging import configure_logging, new_request_id, request_id_var


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a correlation id to every request and echo it back."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or new_request_id()
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.debug)

    app = FastAPI(title="CareerFarm API")

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(me.router)

    install_error_handlers(app)
    return app


app = create_app()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `19 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/app/logging.py backend/app/errors.py backend/app/main.py backend/tests/test_errors.py
git commit -m "feat(obs): structured logging, request ids, and a typed error taxonomy"
```

---

### Task 4: Security headers, docs gating, and rate limiting

**Files:**
- Create: `backend/app/middleware.py`
- Create: `backend/app/limiter.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_security.py`

**Interfaces:**
- Consumes: `Settings.is_production` (Task 1).
- Produces: `SecurityHeadersMiddleware`, `limiter: Limiter`, `install_rate_limiting(app) -> None`. Phase 3 decorates the upload route with `@limiter.limit("5/minute")`; Phase 2 decorates nothing (auth happens in Supabase, not here).

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_security.py`:

```python
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]


def test_hsts_only_in_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev = TestClient(create_app())
    assert "Strict-Transport-Security" not in dev.get("/health").headers

    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod = TestClient(create_app())
    assert "max-age=" in prod.get("/health").headers["Strict-Transport-Security"]


def test_docs_disabled_in_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod = TestClient(create_app())
    assert prod.get("/docs").status_code == 404
    assert prod.get("/openapi.json").status_code == 404


def test_docs_enabled_in_development(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev = TestClient(create_app())
    assert dev.get("/openapi.json").status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_security.py -q`
Expected: FAIL with `KeyError: 'x-content-type-options'`

- [ ] **Step 3: Create `backend/app/middleware.py`**

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# This service returns JSON only — it never serves HTML or scripts, so the
# policy can be maximally restrictive. The frontend sets its own CSP.
_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, production: bool) -> None:
        super().__init__(app)
        self.production = production

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", _CSP)
        if self.production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response
```

- [ ] **Step 4: Create `backend/app/limiter.py`**

```python
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request


def client_key(request: Request) -> str:
    """Real client IP behind Railway's proxy, falling back to the socket peer.

    get_remote_address alone would rate-limit the proxy, i.e. everyone as one.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_key, default_limits=["120/minute"])


def install_rate_limiting(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
```

- [ ] **Step 5: Wire both into `create_app()`**

In `backend/app/main.py`, add the imports:

```python
from app.limiter import install_rate_limiting
from app.middleware import SecurityHeadersMiddleware
```

Change the `FastAPI(...)` construction and middleware block to:

```python
    app = FastAPI(
        title="CareerFarm API",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        SecurityHeadersMiddleware, production=settings.is_production
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_rate_limiting(app)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `23 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/app/middleware.py backend/app/limiter.py backend/app/main.py backend/tests/test_security.py
git commit -m "feat(sec): security headers, production docs gating, and IP rate limiting"
```

---

### Task 5: Core models

**Files:**
- Create: `backend/app/models/__init__.py`, `base.py`, `profile.py`, `skill.py`, `goal.py`, `growth_event.py`, `usage.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Consumes: `Base` from `app.db` (Task 2).
- Produces: `CareerProfile`, `Skill`, `Goal`, `GrowthEvent`, `AiUsage`. Tasks 7–10 and every later phase import these from `app.models`.

Generic SQLAlchemy types (`Uuid`, `JSON` with a `JSONB` variant) are used deliberately so the sqlite in-memory test database works while Postgres still gets native types.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_models.py`:

```python
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import AiUsage, CareerProfile, Goal, GrowthEvent, Skill


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_profile_defaults_and_skill_cascade():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4(), email="a@b.com")
    db.add(profile)
    db.commit()

    assert profile.level == 1
    assert profile.xp == 0
    assert profile.streak_days == 0
    assert profile.created_at is not None

    db.add(Skill(profile_id=profile.id, name="Python", source="cv", mastery=40))
    db.commit()
    assert len(profile.skills) == 1

    db.delete(profile)
    db.commit()
    assert db.query(Skill).count() == 0


def test_growth_event_stores_json_payload():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    event = GrowthEvent(
        profile_id=profile.id,
        type="skill_discovered",
        payload={"skill": "Docker"},
        xp_awarded=10,
    )
    db.add(event)
    db.commit()
    assert db.query(GrowthEvent).one().payload == {"skill": "Docker"}


def test_goal_and_usage_defaults():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    goal = Goal(profile_id=profile.id, title="Learn Kubernetes")
    usage = AiUsage(profile_id=profile.id, day="2026-07-27", feature="cv_analysis")
    db.add_all([goal, usage])
    db.commit()

    assert goal.status == "active"
    assert goal.progress == 0
    assert usage.calls == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models'`

- [ ] **Step 3: Create `backend/app/models/base.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

# Native JSONB on Postgres, plain JSON on SQLite so tests can run in memory.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

- [ ] **Step 4: Create `backend/app/models/profile.py`**

```python
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class CareerProfile(UUIDPrimaryKey, Timestamps, Base):
    """The canonical record. Every feature reads and writes this."""

    __tablename__ = "career_profiles"

    # Supabase auth.users.id. Not a FK — that table lives in another schema.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320))

    full_name: Mapped[str | None] = mapped_column(String(200))
    current_role: Mapped[str | None] = mapped_column(String(200))
    target_role: Mapped[str | None] = mapped_column(String(200))
    years_of_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    seniority_level: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[str | None] = mapped_column(Text)

    # Parse-and-discard: the extracted text is kept, the uploaded file is not.
    cv_text: Mapped[str | None] = mapped_column(Text)

    level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    xp: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    streak_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_active_on: Mapped[date | None] = mapped_column(Date)

    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
```

- [ ] **Step 5: Create the remaining four model files**

`backend/app/models/skill.py`:

```python
import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Skill(UUIDPrimaryKey, Timestamps, Base):
    """A plant on the farm. Mastery drives how grown it renders."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_skill_name"),)

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(60))
    mastery: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # cv | job_match | skill_gap | roadmap | manual
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    profile: Mapped["CareerProfile"] = relationship(back_populates="skills")
```

`backend/app/models/goal.py`:

```python
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Goal(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "goals"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # active | done | abandoned
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    progress: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    target_date: Mapped[date | None] = mapped_column(Date)

    profile: Mapped["CareerProfile"] = relationship(back_populates="goals")
```

`backend/app/models/growth_event.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import JSONType


class GrowthEvent(Base):
    """Append-only. Never updated, never deleted. The Farm reads this."""

    __tablename__ = "growth_events"
    __table_args__ = (
        Index("ix_growth_events_profile_created", "profile_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # skill_discovered | skill_leveled | goal_completed | cv_analyzed
    # | job_matched | gap_analyzed | roadmap_created | interview_completed
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSONType, nullable=False, default=dict, server_default="{}"
    )
    xp_awarded: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

`backend/app/models/usage.py`:

```python
import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AiUsage(Base):
    """One row per (profile, day, feature). Backs the daily AI quota."""

    __tablename__ = "ai_usage"
    __table_args__ = (
        UniqueConstraint("profile_id", "day", "feature", name="uq_ai_usage_slot"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    feature: Mapped[str] = mapped_column(String(40), nullable=False)
    calls: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
```

`backend/app/models/__init__.py`:

```python
from app.models.goal import Goal
from app.models.growth_event import GrowthEvent
from app.models.profile import CareerProfile
from app.models.skill import Skill
from app.models.usage import AiUsage

__all__ = ["AiUsage", "CareerProfile", "Goal", "GrowthEvent", "Skill"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `26 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/app/models backend/tests/test_models.py
git commit -m "feat(models): career profile, skills, goals, growth events, ai usage"
```

---

### Task 6: Migrations — core schema and deny-by-default RLS

**Files:**
- Create: `backend/migrations/versions/0002_core_schema.py`
- Create: `backend/migrations/versions/0003_rls_deny_by_default.py`
- Modify: `backend/migrations/env.py`

**Interfaces:**
- Consumes: `app.models` (Task 5), `Settings.migration_database_url` (already added in Phase 0).
- Produces: the physical schema. Every later migration chains off `0003_rls_deny_by_default`.

- [ ] **Step 1: Make Alembic see the models**

In `backend/migrations/env.py`, below the existing `from app.db import Base`:

```python
import app.models  # noqa: F401  — registers every model on Base.metadata
```

Without this, `--autogenerate` produces empty migrations.

- [ ] **Step 2: Generate the schema migration**

```bash
uv run alembic revision --autogenerate -m "core schema" --rev-id 0002_core_schema
```

Open the generated file. Confirm it creates `career_profiles`, `skills`, `goals`, `growth_events`, `ai_usage` with the indexes and unique constraints from Task 5. Set `down_revision = "0001_baseline"` if autogenerate did not.

Autogenerate is a starting point, not an oracle — read every line before trusting it.

- [ ] **Step 3: Write the RLS migration**

Create `backend/migrations/versions/0003_rls_deny_by_default.py`:

```python
"""Enable RLS on every application table with no permissive policy.

The backend connects as a role that bypasses RLS, so authorization for the
API path lives in the service layer. This exists so the browser's Supabase
anon key — which must be public for Auth to work — can read and write
nothing if it leaks. Adding a permissive policy would defeat the purpose.
"""
from alembic import op

revision = "0003_rls_deny_by_default"
down_revision = "0002_core_schema"
branch_labels = None
depends_on = None

TABLES = ["career_profiles", "skills", "goals", "growth_events", "ai_usage"]


def upgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
```

> **Read this before running.** `FORCE ROW LEVEL SECURITY` applies RLS to the table *owner* as well. If your `DATABASE_URL` role owns these tables, forcing RLS with zero policies locks **your own backend** out of them. Decide deliberately:
>
> - **If the backend connects as the table owner** (the default when you run migrations as `postgres`): drop the two `FORCE` lines. `ENABLE` alone already denies the `anon` and `authenticated` roles, which is the entire threat being addressed.
> - **If you create a separate non-owner application role** (recommended, and what Phase 8's runbook assumes): keep `FORCE`, and grant that role explicit `SELECT, INSERT, UPDATE, DELETE` plus a `BYPASSRLS` attribute, or add policies scoped to it.
>
> Start without `FORCE`. Add the separate role in Phase 8 when the deploy topology is settled.

- [ ] **Step 4: Run the migrations against a real Supabase database**

Set `DIRECT_DATABASE_URL` in `.env` to the direct connection string (port 5432), then:

```bash
uv run alembic upgrade head
```

Expected: `Running upgrade 0001_baseline -> 0002_core_schema`, then `-> 0003_rls_deny_by_default`.

The transaction pooler on port 6543 cannot run this — DDL needs a session-level connection. That is why `migration_database_url` exists.

- [ ] **Step 5: Verify RLS is on and no policies exist**

Run this in the Supabase SQL editor:

```sql
SELECT c.relname, c.relrowsecurity, count(p.polname) AS policies
FROM pg_class c
LEFT JOIN pg_policy p ON p.polrelid = c.oid
WHERE c.relname IN ('career_profiles','skills','goals','growth_events','ai_usage')
GROUP BY c.relname, c.relrowsecurity;
```

Expected: five rows, `relrowsecurity = true`, `policies = 0`.

- [ ] **Step 6: Verify the downgrade path works**

```bash
uv run alembic downgrade 0001_baseline && uv run alembic upgrade head
```

Expected: both succeed. A migration you have never reversed is not a migration you can roll back at 3am.

- [ ] **Step 7: Commit**

```bash
git add backend/migrations
git commit -m "feat(db): core schema migration and deny-by-default RLS"
```

---

### Task 7: XP and levelling

**Files:**
- Create: `backend/app/services/__init__.py`, `backend/app/services/xp_service.py`
- Test: `backend/tests/test_xp_service.py`

**Interfaces:**
- Consumes: `GrowthEvent`, `CareerProfile` (Task 5).
- Produces:
  - `class LevelInfo(NamedTuple)` with fields `level: int`, `title: str`, `xp_in_level: int`, `xp_for_next: int`
  - `def level_for_xp(xp: int) -> LevelInfo`
  - `def record_event(db, profile_id, type, payload, xp) -> GrowthEvent`
  - `XP_AWARDS: dict[str, int]`

  The frontend `Topbar` at `frontend/src/components/layout/topbar.tsx:17` renders `xp / xpForNext`, so `xp_in_level` (not total xp) is what `GET /profile` must return as `xp`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_xp_service.py`:

```python
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import CareerProfile, GrowthEvent
from app.services import xp_service


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


@pytest.mark.parametrize(
    "xp,level,xp_in_level,xp_for_next",
    [
        (0, 1, 0, 100),
        (99, 1, 99, 100),
        (100, 2, 0, 150),
        (249, 2, 149, 150),
        (250, 3, 0, 200),
    ],
)
def test_level_curve(xp, level, xp_in_level, xp_for_next):
    info = xp_service.level_for_xp(xp)
    assert (info.level, info.xp_in_level, info.xp_for_next) == (
        level,
        xp_in_level,
        xp_for_next,
    )


def test_level_title_is_stable_and_capped():
    assert xp_service.level_for_xp(0).title == "Seedling"
    assert xp_service.level_for_xp(10_000_000).title == xp_service.LEVEL_TITLES[-1]


def test_record_event_appends_and_awards_xp():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    xp_service.record_event(
        db, profile.id, "cv_analyzed", {"analysis_id": "x"}, xp=50
    )
    xp_service.record_event(db, profile.id, "skill_discovered", {"skill": "Go"}, xp=10)

    db.refresh(profile)
    assert profile.xp == 60
    assert profile.level == 1
    assert db.query(GrowthEvent).count() == 2


def test_record_event_levels_the_profile_up():
    db = _session()
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()

    xp_service.record_event(db, profile.id, "cv_analyzed", {}, xp=120)
    db.refresh(profile)
    assert profile.level == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_xp_service.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services'`

- [ ] **Step 3: Create `backend/app/services/xp_service.py`**

```python
import uuid
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.models import CareerProfile, GrowthEvent

LEVEL_TITLES = [
    "Seedling",
    "Sprout",
    "Sapling",
    "Grower",
    "Cultivator",
    "Gardener",
    "Orchardist",
    "Harvester",
    "Farmstead",
    "Homesteader",
]

# XP required for level 2 is _BASE; each subsequent level costs _STEP more.
_BASE = 100
_STEP = 50

XP_AWARDS = {
    "cv_analyzed": 50,
    "skill_discovered": 10,
    "skill_leveled": 15,
    "job_matched": 20,
    "gap_analyzed": 20,
    "roadmap_created": 40,
    "goal_completed": 60,
    "interview_completed": 75,
}


class LevelInfo(NamedTuple):
    level: int
    title: str
    xp_in_level: int
    xp_for_next: int


def level_for_xp(xp: int) -> LevelInfo:
    """Map total lifetime XP to a level and progress within that level."""
    level = 1
    remaining = max(xp, 0)
    cost = _BASE
    while remaining >= cost:
        remaining -= cost
        level += 1
        cost += _STEP
    title = LEVEL_TITLES[min(level - 1, len(LEVEL_TITLES) - 1)]
    return LevelInfo(level=level, title=title, xp_in_level=remaining, xp_for_next=cost)


def record_event(
    db: Session,
    profile_id: uuid.UUID,
    type: str,
    payload: dict,
    xp: int = 0,
) -> GrowthEvent:
    """Append a growth event and re-derive the profile's level from total XP.

    The event log is the source of truth; `profile.xp` and `profile.level` are
    a denormalised cache so the topbar does not aggregate on every render.
    """
    event = GrowthEvent(
        profile_id=profile_id, type=type, payload=payload or {}, xp_awarded=xp
    )
    db.add(event)

    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")
    profile.xp += xp
    profile.level = level_for_xp(profile.xp).level

    db.commit()
    db.refresh(event)
    return event
```

Create an empty `backend/app/services/__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `33 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/services backend/tests/test_xp_service.py
git commit -m "feat(xp): growth event log with level curve"
```

---

### Task 8: AI quota

**Files:**
- Create: `backend/app/services/quota_service.py`
- Test: `backend/tests/test_quota_service.py`

**Interfaces:**
- Consumes: `AiUsage` (Task 5), `QuotaExceeded` (Task 3).
- Produces:
  - `DAILY_LIMITS: dict[str, int]`
  - `def consume(db: Session, profile_id: uuid.UUID, feature: str) -> int` — returns the new call count, raises `QuotaExceeded` when the limit is already reached
  - `def usage_today(db: Session, profile_id: uuid.UUID) -> dict[str, int]`

  Phases 3–7 call `consume()` immediately before every chain invoke.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_quota_service.py`:

```python
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.errors import QuotaExceeded
from app.models import CareerProfile
from app.services import quota_service


def _session_and_profile():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    profile = CareerProfile(user_id=uuid.uuid4())
    db.add(profile)
    db.commit()
    return db, profile


def test_consume_increments_and_returns_count():
    db, profile = _session_and_profile()
    assert quota_service.consume(db, profile.id, "cv_analysis") == 1
    assert quota_service.consume(db, profile.id, "cv_analysis") == 2


def test_consume_raises_once_limit_is_reached(monkeypatch):
    db, profile = _session_and_profile()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 2)

    quota_service.consume(db, profile.id, "cv_analysis")
    quota_service.consume(db, profile.id, "cv_analysis")
    with pytest.raises(QuotaExceeded) as exc:
        quota_service.consume(db, profile.id, "cv_analysis")

    assert exc.value.extra["feature"] == "cv_analysis"
    assert exc.value.extra["limit"] == 2


def test_features_have_independent_budgets(monkeypatch):
    db, profile = _session_and_profile()
    monkeypatch.setitem(quota_service.DAILY_LIMITS, "cv_analysis", 1)
    quota_service.consume(db, profile.id, "cv_analysis")
    assert quota_service.consume(db, profile.id, "job_match") == 1


def test_unknown_feature_is_a_programming_error():
    db, profile = _session_and_profile()
    with pytest.raises(ValueError, match="Unknown AI feature"):
        quota_service.consume(db, profile.id, "not_a_feature")


def test_usage_today_reports_per_feature_counts():
    db, profile = _session_and_profile()
    quota_service.consume(db, profile.id, "cv_analysis")
    quota_service.consume(db, profile.id, "job_match")
    quota_service.consume(db, profile.id, "job_match")
    assert quota_service.usage_today(db, profile.id) == {
        "cv_analysis": 1,
        "job_match": 2,
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_quota_service.py -q`
Expected: FAIL with `ImportError: cannot import name 'quota_service'`

- [ ] **Step 3: Create `backend/app/services/quota_service.py`**

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import QuotaExceeded
from app.models import AiUsage

# Calls per user per UTC day. Tuned so a genuine user never notices and an
# abuser burns out fast. Raise deliberately, with the Gemini bill in view.
DAILY_LIMITS: dict[str, int] = {
    "cv_analysis": 10,
    "job_match": 20,
    "skill_gap": 20,
    "resume_optimizer": 10,
    "roadmap": 10,
    "interview_turn": 60,
    "chat_message": 100,
}


def _today():
    return datetime.now(timezone.utc).date()


def _row(db: Session, profile_id: uuid.UUID, feature: str, day) -> AiUsage:
    stmt = (
        select(AiUsage)
        .where(
            AiUsage.profile_id == profile_id,
            AiUsage.day == day,
            AiUsage.feature == feature,
        )
        .with_for_update()
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is not None:
        return row

    row = AiUsage(profile_id=profile_id, day=day, feature=feature, calls=0)
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        # Concurrent request created the slot first. Re-read it.
        db.rollback()
        row = db.execute(stmt).scalar_one()
    return row


def consume(db: Session, profile_id: uuid.UUID, feature: str) -> int:
    """Charge one AI call. Raises QuotaExceeded when today's budget is spent.

    Call this immediately before invoking a chain, never after — a failed
    generation still costs tokens.
    """
    limit = DAILY_LIMITS.get(feature)
    if limit is None:
        raise ValueError(f"Unknown AI feature: {feature!r}")

    day = _today()
    row = _row(db, profile_id, feature, day)

    if row.calls >= limit:
        db.rollback()
        raise QuotaExceeded(
            f"Daily limit for {feature} reached. Try again tomorrow.",
            feature=feature,
            limit=limit,
        )

    row.calls += 1
    db.commit()
    return row.calls


def usage_today(db: Session, profile_id: uuid.UUID) -> dict[str, int]:
    rows = db.execute(
        select(AiUsage.feature, AiUsage.calls).where(
            AiUsage.profile_id == profile_id, AiUsage.day == _today()
        )
    ).all()
    return {feature: calls for feature, calls in rows}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `38 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/quota_service.py backend/tests/test_quota_service.py
git commit -m "feat(quota): per-user daily AI call budget"
```

---

### Task 9: Profile service

**Files:**
- Create: `backend/app/services/profile_service.py`
- Create: `backend/app/schemas/__init__.py`, `backend/app/schemas/profile.py`
- Test: `backend/tests/test_profile_service.py`

**Interfaces:**
- Consumes: `CareerProfile`, `Skill` (Task 5); `AuthUser` from `app.auth`; `xp_service.record_event` (Task 7).
- Produces:
  - `ProfileOut`, `ProfileUpdate`, `SkillIn`, `SkillOut` (Pydantic)
  - `def get_or_create(db: Session, user: AuthUser) -> CareerProfile`
  - `def update(db: Session, profile_id: uuid.UUID, patch: ProfileUpdate) -> CareerProfile`
  - `def upsert_skills(db, profile_id, skills: list[SkillIn], source: str) -> list[Skill]`
  - `def to_out(profile: CareerProfile) -> ProfileOut`

  Phase 3 calls `upsert_skills(..., source="cv")`. Phase 4 calls it with `source="job_match"`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_profile_service.py`:

```python
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import AuthUser
from app.db import Base
from app.models import GrowthEvent
from app.schemas.profile import ProfileUpdate, SkillIn
from app.services import profile_service


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_get_or_create_is_idempotent():
    db = _session()
    user = AuthUser(id=str(uuid.uuid4()), email="a@b.com")

    first = profile_service.get_or_create(db, user)
    second = profile_service.get_or_create(db, user)

    assert first.id == second.id
    assert first.email == "a@b.com"


def test_update_applies_only_provided_fields():
    db = _session()
    user = AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    profile = profile_service.get_or_create(db, user)

    profile_service.update(db, profile.id, ProfileUpdate(target_role="Staff Engineer"))
    profile_service.update(db, profile.id, ProfileUpdate(full_name="Nour Hassan"))

    db.refresh(profile)
    assert profile.target_role == "Staff Engineer"
    assert profile.full_name == "Nour Hassan"


def test_upsert_skills_dedupes_case_insensitively_and_emits_events():
    db = _session()
    user = AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    profile = profile_service.get_or_create(db, user)

    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="Python"), SkillIn(name="Docker")], source="cv"
    )
    profile_service.upsert_skills(
        db, profile.id, [SkillIn(name="python"), SkillIn(name="Go")], source="cv"
    )

    names = sorted(s.name for s in profile_service.get_or_create(db, user).skills)
    assert names == ["Docker", "Go", "Python"]

    discovered = db.query(GrowthEvent).filter_by(type="skill_discovered").count()
    assert discovered == 3  # one per genuinely new skill, not per submission


def test_to_out_reports_xp_within_the_current_level():
    db = _session()
    user = AuthUser(id=str(uuid.uuid4()), email="a@b.com")
    profile = profile_service.get_or_create(db, user)
    profile.xp = 120
    db.commit()

    out = profile_service.to_out(profile)
    assert out.level == 2
    assert out.xp == 20
    assert out.xp_for_next == 150
    assert out.level_title == "Sprout"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profile_service.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas'`

- [ ] **Step 3: Create `backend/app/schemas/profile.py`**

```python
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
    has_cv: bool
    level: int
    level_title: str
    xp: int          # XP within the current level, not lifetime
    xp_for_next: int
    streak_days: int
    created_at: datetime
```

`has_cv` is a boolean, not `cv_text`. The full extracted CV is potentially thousands of tokens and the client never needs it.

Create an empty `backend/app/schemas/__init__.py`.

- [ ] **Step 4: Create `backend/app/services/profile_service.py`**

```python
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


def update(
    db: Session, profile_id: uuid.UUID, patch: ProfileUpdate
) -> CareerProfile:
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
    create a second plant next to "Python" from the CV.
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `42 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas backend/app/services/profile_service.py backend/tests/test_profile_service.py
git commit -m "feat(profile): canonical career profile service with skill merging"
```

---

### Task 10: Dependencies and the profile router

**Files:**
- Create: `backend/app/deps.py`
- Create: `backend/app/api/profile.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_profile_api.py`

**Interfaces:**
- Consumes: everything from Tasks 7–9.
- Produces:
  - `DbSession = Annotated[Session, Depends(get_db)]`
  - `CurrentProfile = Annotated[CareerProfile, Depends(get_current_profile)]`

  Every router from Phase 3 onwards takes exactly these two annotations. That is how `profile_id` reaches the service layer, and it is why no route ever reads a `profile_id` from the client.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_profile_api.py`:

```python
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.main import create_app
from tests.conftest import make_token


@pytest.fixture
def api():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    db.close()


def _auth(sub=None):
    return {"Authorization": f"Bearer {make_token(sub=sub or str(uuid.uuid4()))}"}


def test_profile_requires_auth(api):
    assert api.get("/profile").status_code == 401


def test_get_profile_creates_it_on_first_call(api):
    headers = _auth()
    r = api.get("/profile", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["level"] == 1
    assert body["xp"] == 0
    assert body["has_cv"] is False
    assert "cv_text" not in body  # never ship the raw CV to the client

    again = api.get("/profile", headers=headers)
    assert again.json()["id"] == body["id"]


def test_two_users_get_separate_profiles(api):
    a = api.get("/profile", headers=_auth("11111111-1111-1111-1111-111111111111"))
    b = api.get("/profile", headers=_auth("22222222-2222-2222-2222-222222222222"))
    assert a.json()["id"] != b.json()["id"]


def test_patch_profile(api):
    headers = _auth()
    api.get("/profile", headers=headers)
    r = api.patch(
        "/profile", headers=headers, json={"target_role": "Staff Engineer"}
    )
    assert r.status_code == 200
    assert r.json()["target_role"] == "Staff Engineer"


def test_post_and_get_skills(api):
    headers = _auth()
    api.get("/profile", headers=headers)

    r = api.post(
        "/profile/skills",
        headers=headers,
        json={"skills": [{"name": "Python", "mastery": 60}]},
    )
    assert r.status_code == 200

    skills = api.get("/profile/skills", headers=headers).json()
    assert [s["name"] for s in skills] == ["Python"]
    assert skills[0]["source"] == "manual"
```

Note `make_token` currently defaults `sub="user-123"`, which is not a UUID. Change its default in `tests/conftest.py` to `sub=str(uuid.uuid4())` and update `test_auth.py::test_me_valid` to pass and assert an explicit `sub`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_profile_api.py -q`
Expected: FAIL with `404 != 401` (the route does not exist yet)

- [ ] **Step 3: Create `backend/app/deps.py`**

```python
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

    Routes depend on this rather than accepting a profile_id, so a client can
    never address another user's data.
    """
    return profile_service.get_or_create(db, user)


CurrentProfile = Annotated[CareerProfile, Depends(get_current_profile)]
```

- [ ] **Step 4: Create `backend/app/api/profile.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.deps import CurrentProfile, DbSession
from app.schemas.profile import ProfileOut, ProfileUpdate, SkillIn, SkillOut
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


class SkillsPayload(BaseModel):
    skills: list[SkillIn] = Field(min_length=1, max_length=100)


@router.get("", response_model=ProfileOut)
def read_profile(profile: CurrentProfile) -> ProfileOut:
    return profile_service.to_out(profile)


@router.patch("", response_model=ProfileOut)
def patch_profile(
    patch: ProfileUpdate, profile: CurrentProfile, db: DbSession
) -> ProfileOut:
    updated = profile_service.update(db, profile.id, patch)
    return profile_service.to_out(updated)


@router.get("/skills", response_model=list[SkillOut])
def read_skills(profile: CurrentProfile) -> list[SkillOut]:
    return [SkillOut.model_validate(s) for s in profile.skills]


@router.post("/skills", response_model=list[SkillOut])
def add_skills(
    payload: SkillsPayload, profile: CurrentProfile, db: DbSession
) -> list[SkillOut]:
    skills = profile_service.upsert_skills(
        db, profile.id, payload.skills, source="manual"
    )
    return [SkillOut.model_validate(s) for s in skills]
```

The `max_length=100` on the skills list is deliberate — an unbounded list would let one request create unbounded rows.

- [ ] **Step 5: Register the router**

In `backend/app/main.py`, change the import and registration:

```python
from app.api import health, me, profile
```

```python
    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(profile.router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `47 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/app/deps.py backend/app/api/profile.py backend/app/main.py backend/tests/test_profile_api.py backend/tests/conftest.py backend/tests/test_auth.py
git commit -m "feat(api): profile and skills endpoints"
```

---

### Task 11: Health check that actually checks

Railway will point its healthcheck at `/health`. A route that returns `ok` unconditionally reports a database outage as healthy.

**Files:**
- Modify: `backend/app/api/health.py`
- Modify: `backend/tests/test_health.py`

**Interfaces:**
- Consumes: `DbSession` (Task 10).
- Produces: `GET /health` → `200 {"status":"ok","database":"ok"}` or `503 {"status":"degraded","database":"error"}`.

- [ ] **Step 1: Write the failing test**

Replace `backend/tests/test_health.py` with:

```python
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import create_app


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_health_reports_degraded_when_db_is_down():
    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app = create_app()
    app.dependency_overrides[get_db] = lambda: BrokenSession()
    r = TestClient(app).get("/health")

    assert r.status_code == 503
    assert r.json()["status"] == "degraded"
    assert "connection refused" not in r.text  # no internals in a public probe
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_health.py -q`
Expected: FAIL — the response is `{"status": "ok"}` with no `database` key

- [ ] **Step 3: Rewrite `backend/app/api/health.py`**

```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession
from app.logging import get_logger

router = APIRouter(tags=["health"])
log = get_logger(__name__)


@router.get("/health")
def health(db: DbSession):
    """Liveness plus a real database round trip. Railway probes this."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.exception("health_db_check_failed")
        return JSONResponse(
            status_code=503, content={"status": "degraded", "database": "error"}
        )
    return {"status": "ok", "database": "ok"}
```

- [ ] **Step 4: Point the shared client fixture at a real session**

`tests/conftest.py`'s `client` fixture builds the app with no DB override, so `/health` would try to open the sqlite memory URL from `DATABASE_URL`. Add the override there:

```python
@pytest.fixture
def client():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.db import Base, get_db

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    db.close()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `48 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/health.py backend/tests/test_health.py backend/tests/conftest.py
git commit -m "feat(health): probe the database in the health check"
```

---

### Task 12: Sentry, and an end-to-end pass against real Supabase

**Files:**
- Modify: `backend/app/main.py`
- Modify: `docs/architecture.md`
- Test: manual, against a provisioned Supabase project

**Interfaces:**
- Consumes: `Settings.sentry_dsn` (Task 1).
- Produces: nothing new. This task closes the phase.

- [ ] **Step 1: Initialise Sentry when a DSN is present**

In `backend/app/main.py`, at the top of `create_app()` after `configure_logging(...)`:

```python
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
```

`send_default_pii=False` matters — CV text and chat messages must never reach Sentry.

- [ ] **Step 2: Run the whole suite**

Run: `uv run pytest -q`
Expected: `48 passed`

- [ ] **Step 3: Run against real Supabase**

Fill `.env` with a real Supabase project, then:

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000
```

- [ ] **Step 4: Verify by hand**

```bash
curl -s localhost:8000/health
```
Expected: `{"status":"ok","database":"ok"}`

```bash
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/profile
```
Expected: `401`

With a real Supabase access token in `$TOKEN`:

```bash
curl -s localhost:8000/profile -H "Authorization: Bearer $TOKEN"
```
Expected: a `ProfileOut` JSON body with `"level": 1`, and a new row in `career_profiles`.

> **If this returns 401 with a valid token, stop and read the JWT risk in the roadmap.** `app/auth.py` verifies HS256 against a shared secret; new Supabase projects issue asymmetric keys. Finding this now costs one afternoon. Finding it in Phase 8 costs the launch.

- [ ] **Step 5: Confirm the security headers on a real response**

```bash
curl -sI localhost:8000/health
```
Expected: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`, and `X-Request-ID` all present.

- [ ] **Step 6: Update the build status table**

In `docs/architecture.md`, change the row for sub-project 2 from `⬜ Not started` to `✅ Done`, and replace the "Core data model (planned)" heading with the tables actually shipped.

- [ ] **Step 7: Commit**

```bash
git add backend/app/main.py docs/architecture.md
git commit -m "feat(obs): optional Sentry init; close phase 1"
```

---

## Phase 1 exit criteria

Every one of these must hold before Phase 3 starts:

- [ ] `uv run pytest -q` → `48 passed`
- [ ] `uv run alembic upgrade head` succeeds against real Supabase, and `downgrade` back to `0001_baseline` also succeeds
- [ ] All five tables report `relrowsecurity = true` with zero policies
- [ ] `GET /health` returns `database: ok`; stopping the database turns it into a 503
- [ ] `GET /profile` with no token → 401; with a valid token → auto-created profile
- [ ] Two different tokens receive two different profile ids
- [ ] `quota_service.consume` raises `QuotaExceeded` on the 11th `cv_analysis` call in a UTC day
- [ ] A deliberately raised exception produces a JSON log line containing a `request_id` that matches the `X-Request-ID` response header
- [ ] No response body anywhere contains a stack trace, an exception message, or `cv_text`

## What Phase 1 deliberately does not do

- No frontend changes. Phase 2 owns those.
- No AI calls. `quota_service` is built and tested but nothing consumes it until Phase 3.
- No RLS policies. Deny-by-default is the design, not an oversight — see the roadmap.
- No `documents`/`embeddings` tables. Phase 7 adds them, with `pgvector` already installed here so the dependency set stops churning.
