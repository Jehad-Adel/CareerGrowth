# Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A bootable, tested FastAPI backend wired to Supabase (Postgres + auth) with migrations, config, and docs — the base every feature builds on.

**Architecture:** Single `backend/` app managed by uv. FastAPI app factory includes routers; config via pydantic-settings; SQLAlchemy engine/session; Alembic for schema (baseline enables pgvector); Supabase JWT verified locally as a FastAPI dependency. No feature logic.

**Tech Stack:** Python 3.11, uv, FastAPI, Uvicorn, Pydantic v2 + pydantic-settings, SQLAlchemy 2.0 (sync), Alembic, psycopg2, PyJWT, pytest + httpx.

## Global Constraints

- Python `>=3.11` (uses `X | None` syntax).
- Backend lives in `backend/`; run commands assume cwd = `backend/`.
- Supabase JWT verified locally (HS256, `SUPABASE_JWT_SECRET`, audience `authenticated`) — no network call.
- Sync SQLAlchemy. Async deferred.
- `.env` is gitignored; `.env.example` is committed.
- TDD: failing test first, minimal code, green, commit.
- Spec: [2026-07-23-foundation-design.md](../specs/2026-07-23-foundation-design.md).

---

## File Structure

```
backend/
  pyproject.toml  uv.lock  .env.example
  alembic.ini  migrations/env.py  migrations/versions/*_baseline.py
  app/
    __init__.py
    main.py        # app factory (CORS, routers, exception handler)
    config.py      # Settings + get_settings()
    db.py          # engine, SessionLocal, Base, get_db
    auth.py        # AuthUser, get_current_user
    api/
      __init__.py
      health.py    # GET /health
      me.py        # GET /me
  tests/
    __init__.py
    conftest.py    # client fixture, make_token helper, test env
    test_health.py
    test_auth.py
README.md
```

---

### Task 1: Bootstrap project + health endpoint

**Files:**
- Delete: `main.py`, `frontend/` (entire dir), all empty `backend/**/*.py` stubs
- Create: `backend/pyproject.toml` (via uv), `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/api/__init__.py`, `backend/app/api/health.py`, `backend/tests/__init__.py`, `backend/tests/conftest.py`, `backend/tests/test_health.py`
- Create: `backend/.gitignore` entry for `.env`

**Interfaces:**
- Produces: `app.main:create_app() -> FastAPI`, `app.main:app`, `GET /health -> {"status":"ok"}`

- [ ] **Step 1: Clean slate — remove old skeleton**

```bash
cd backend
git rm -r --quiet ../main.py ../frontend
find . -name '*.py' -empty -delete
find . -type d -empty -delete
```
Keep `backend/` itself; recreate structure below.

- [ ] **Step 2: Init uv project + add deps**

```bash
cd backend
uv init --name careerfarm-backend --python 3.11 --no-workspace
rm -f hello.py main.py   # remove uv's sample module if created
uv add "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2.7" "pydantic-settings>=2.3" "sqlalchemy>=2.0" "alembic>=1.13" "psycopg2-binary>=2.9" "pyjwt>=2.8"
uv add --dev "pytest>=8" "httpx>=0.27"
```
Expected: `pyproject.toml` + `uv.lock` created, `.venv/` populated.

- [ ] **Step 3: Write the failing test**

`backend/tests/__init__.py` — empty file.
`backend/tests/conftest.py`:
```python
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
```
`backend/tests/test_health.py`:
```python
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'` (config/main not created yet).

- [ ] **Step 5: Write minimal implementation**

`backend/app/__init__.py` — empty. `backend/app/api/__init__.py` — empty.
`backend/app/config.py`:
```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    anthropic_api_key: str = ""
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```
`backend/app/api/health.py`:
```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
```
`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CareerFarm API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 7: Verify server boots**

Run: `uv run uvicorn app.main:app --port 8000` then `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`. Ctrl-C to stop.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: bootstrap FastAPI backend with health endpoint"
```

---

### Task 2: Config + .env.example

**Files:**
- Create: `backend/.env.example`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Consumes: `app.config:get_settings`
- Produces: verified `Settings` fields (`database_url`, `supabase_url`, `supabase_jwt_secret`, `anthropic_api_key`, `cors_origins`)

- [ ] **Step 1: Write the failing test**

`backend/tests/test_config.py`:
```python
import importlib

from app.config import get_settings


def test_settings_read_from_env(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "abc123")
    s = get_settings()
    assert s.supabase_jwt_secret == "abc123"
    assert s.cors_origins  # has a default


def test_env_example_lists_required_keys():
    # pytest runs with cwd = backend/
    text = open(".env.example").read()
    for key in ["DATABASE_URL", "SUPABASE_URL", "SUPABASE_JWT_SECRET", "ANTHROPIC_API_KEY"]:
        assert key in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `.env.example` missing (`FileNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

`backend/.env.example`:
```
# Supabase Postgres connection string (Session pooler or direct)
DATABASE_URL=postgresql+psycopg2://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
# Supabase project URL
SUPABASE_URL=https://PROJECT.supabase.co
# Supabase JWT secret (Project Settings -> API -> JWT Secret)
SUPABASE_JWT_SECRET=your-jwt-secret
# Anthropic API key (unused until CV Studio)
ANTHROPIC_API_KEY=sk-ant-...
# Comma-separated allowed CORS origins
CORS_ORIGINS=http://localhost:3000
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add settings config and .env.example"
```

---

### Task 3: Database layer

**Files:**
- Create: `backend/app/db.py`
- Test: `backend/tests/test_db.py`

**Interfaces:**
- Consumes: `app.config:get_settings`
- Produces: `app.db:engine`, `app.db:SessionLocal`, `app.db:Base` (declarative base), `app.db:get_db()` generator dependency yielding a `Session`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_db.py`:
```python
from sqlalchemy import text

from app.db import Base, get_db


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_db_yields_and_closes():
    gen = get_db()
    db = next(gen)
    assert db.execute(text("SELECT 1")).scalar() == 1
    gen.close()  # triggers finally: db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.db'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/db.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
Note: tests set `DATABASE_URL=sqlite+pysqlite:///:memory:` (see conftest), so import-time engine creation succeeds without Postgres.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add SQLAlchemy engine, session, and get_db dependency"
```

---

### Task 4: Alembic + pgvector baseline migration

**Files:**
- Create: `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`, `backend/migrations/versions/0001_baseline.py`

**Interfaces:**
- Consumes: `app.config:get_settings`, `app.db:Base`
- Produces: runnable `alembic upgrade head` that enables the `vector` extension

- [ ] **Step 1: Init Alembic**

```bash
cd backend
uv run alembic init migrations
```
Expected: `alembic.ini` + `migrations/` created.

- [ ] **Step 2: Wire env.py to app settings + Base**

Edit `backend/migrations/env.py`. After `config = context.config`, add:
```python
from app.config import get_settings
from app.db import Base

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata
```
Ensure the top of `env.py` can import `app` (Alembic runs from `backend/`, which is on the path). Remove the default `target_metadata = None` line.

- [ ] **Step 3: Write the baseline migration**

`backend/migrations/versions/0001_baseline.py`:
```python
"""baseline: enable pgvector

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-23
"""
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS vector")
```

- [ ] **Step 4: Apply against Supabase (integration — needs real DATABASE_URL)**

Set a real Supabase `DATABASE_URL` in `backend/.env`, then:
```bash
cd backend
uv run alembic upgrade head
```
Expected: migration `0001_baseline` applies; no error. Verify in Supabase SQL editor: `SELECT * FROM pg_extension WHERE extname = 'vector';` returns a row.
If no Supabase DB is provisioned yet, mark this step blocked and note it in the PR — the migration code is correct and re-runnable.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Alembic with pgvector baseline migration"
```

---

### Task 5: Supabase JWT auth + /me

**Files:**
- Create: `backend/app/auth.py`, `backend/app/api/me.py`
- Modify: `backend/app/main.py` (include `me.router`)
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Consumes: `app.config:get_settings`, `tests.conftest:make_token`
- Produces: `app.auth:AuthUser` (fields `id: str`, `email: str | None`), `app.auth:get_current_user(...) -> AuthUser`, `GET /me -> AuthUser`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_auth.py`:
```python
from tests.conftest import make_token


def test_me_no_token(client):
    assert client.get("/me").status_code == 401


def test_me_bad_signature(client):
    tok = make_token(secret="wrong-secret")
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_expired(client):
    tok = make_token(exp_offset=-10)
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_me_valid(client):
    tok = make_token()
    r = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "user-123"
    assert body["email"] == "a@b.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth.py -v`
Expected: FAIL — `/me` returns 404 (route not defined) / `app.auth` missing.

- [ ] **Step 3: Write minimal implementation**

`backend/app/auth.py`:
```python
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
```
`backend/app/api/me.py`:
```python
from fastapi import APIRouter, Depends

from app.auth import AuthUser, get_current_user

router = APIRouter()


@router.get("/me", response_model=AuthUser)
def read_me(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user
```
Modify `backend/app/main.py` — add import and include:
```python
from app.api import health, me
```
and after the health include:
```python
    app.include_router(me.router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth.py -v`
Expected: PASS (all 4).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: verify Supabase JWT and add /me endpoint"
```

---

### Task 6: Exception handler + README + full acceptance

**Files:**
- Modify: `backend/app/main.py` (global exception handler)
- Create: `README.md`
- Test: `backend/tests/test_errors.py`

**Interfaces:**
- Consumes: `app.main:create_app`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_errors.py`:
```python
from fastapi import APIRouter

from app.main import create_app
from fastapi.testclient import TestClient


def test_unhandled_error_returns_500_json():
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json() == {"detail": "Internal server error"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_errors.py -v`
Expected: FAIL — default 500 body is not `{"detail": "Internal server error"}`.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/main.py`, add imports:
```python
from fastapi.responses import JSONResponse
from starlette.requests import Request
```
Inside `create_app`, before `return app`:
```python
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_errors.py -v`
Expected: PASS.

- [ ] **Step 5: Write README**

`README.md`:
```markdown
# CareerFarm

AI career-growth platform. See [docs/superpowers/specs](docs/superpowers/specs) for architecture.

## Backend setup

Requirements: [uv](https://docs.astral.sh/uv/), a Supabase project.

```bash
cd backend
cp .env.example .env        # fill in DATABASE_URL, SUPABASE_JWT_SECRET, ...
uv sync
uv run alembic upgrade head # enables pgvector
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`.

## Tests

```bash
cd backend
uv run pytest -v
```
```

- [ ] **Step 6: Full acceptance — run everything**

Run: `cd backend && uv run pytest -v`
Expected: all tests PASS (health, config, db, auth, errors).
Run: `uv run uvicorn app.main:app --port 8000` and confirm `/health` → 200.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add global exception handler and README"
```

---

## Self-Review

- **Spec coverage:** clean slate (T1), uv project (T1), app factory + CORS (T1), health (T1), config + .env.example (T2), SQLAlchemy/Base/get_db (T3), Alembic + pgvector baseline (T4), Supabase JWT verify + get_current_user + /me + 401 cases (T5), exception handler + README + acceptance (T6). All spec sections mapped.
- **Placeholders:** none — every step has runnable code/commands.
- **Type consistency:** `get_settings`, `Settings`, `Base`, `get_db`, `AuthUser(id,email)`, `get_current_user`, `create_app`/`app`, `make_token` used consistently across tasks.
- **Deferred (per spec, not gaps):** LLM module, profile/farm tables, feature services, Next.js frontend, deployment.
