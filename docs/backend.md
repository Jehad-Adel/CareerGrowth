# Backend

FastAPI service in `backend/`, managed with [uv](https://docs.astral.sh/uv/). Python 3.11.

## Module map

```
backend/
  pyproject.toml  uv.lock          # deps + lockfile (uv)
  alembic.ini  migrations/         # schema migrations
  app/
    main.py        # create_app(): FastAPI factory — CORS, routers, exception handler
    config.py      # Settings (pydantic-settings), reads root ../../.env; get_settings()
    db.py          # engine, SessionLocal, Base, get_db() dependency
    auth.py        # AuthUser, get_current_user() — verifies Supabase JWT
    api/
      health.py    # GET /health
      me.py        # GET /me
  tests/           # pytest: test_health, test_config, test_db, test_auth, test_errors
```

Each module has one responsibility:

- **config.py** — typed settings from the single root `.env` (loaded by absolute path, so it works from any cwd). `get_settings()` is `lru_cache`d.
- **db.py** — SQLAlchemy 2.0 (sync). `Base` is the declarative base for models; `get_db()` yields a request-scoped session.
- **auth.py** — `get_current_user` reads `Authorization: Bearer <jwt>`, verifies it locally (HS256, `SUPABASE_JWT_SECRET`, audience `authenticated`) — no network call to Supabase. Returns `AuthUser(id, email)`; raises 401 on missing/invalid/expired.
- **main.py** — app factory. Registers routers and a catch-all exception handler that returns `{"detail": "Internal server error"}` with status 500 (no stack traces to clients).

## Endpoints

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/health` | none | `{"status": "ok"}` |
| GET | `/me` | Bearer JWT | `AuthUser {id, email}`; 401 without a valid token |

## Dependencies

`fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg2-binary`, `pyjwt`. Dev: `pytest`, `httpx`.

## Setup & run

Environment comes from the single root `.env` (see [root README](../README.md#environment)).

```bash
cd backend
uv sync
uv run alembic upgrade head     # applies migrations (enables pgvector) — needs a real DATABASE_URL
uv run uvicorn app.main:app --reload --port 8000
```

Check: `curl http://localhost:8000/health` → `{"status":"ok"}`

## Migrations

Alembic, in `backend/migrations/`. `env.py` pulls the URL and `Base.metadata` from the app.

- `0001_baseline` — enables the `vector` (pgvector) extension. No app tables yet; those land with the Career Profile spine.

```bash
uv run alembic revision -m "add profile tables"   # create a new migration
uv run alembic upgrade head                        # apply
```

## Tests

```bash
cd backend
uv run pytest -v
```

Tests inject env vars and use an in-memory SQLite engine (see `tests/conftest.py`), so they run without a real database. JWTs are minted in-test with the configured secret.
