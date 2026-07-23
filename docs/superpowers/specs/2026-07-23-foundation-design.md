# Sub-project 1 — Foundation

**Status:** Approved (2026-07-23)
**Parent:** [System Architecture](2026-07-23-careerfarm-architecture.md)
**Goal:** A bootable, tested FastAPI backend wired to Supabase (Postgres + auth), with migrations, config, and docs — the base every feature builds on. No feature logic.

---

## 1. Scope

**In:**
- Clean slate: delete empty backend stub files and all Streamlit frontend code (`main.py`, `frontend/`). Git history preserves them.
- Backend project via **uv** (`pyproject.toml`, `uv.lock`).
- FastAPI app factory with CORS, health check, and an auth-proving `/me` endpoint.
- Config via `pydantic-settings`.
- SQLAlchemy engine/session + Base.
- Alembic initialized; first (baseline) migration enables the `pgvector` extension only.
- Supabase JWT verification as a FastAPI dependency (`get_current_user`).
- Tests (pytest + httpx) for health and auth, written first (TDD).
- README setup/run instructions.

**Out (later sub-projects):**
- LLM / `llm` module (arrives with CV Studio, step 3).
- Profile, skills, goals, growth_events tables (step 2).
- Any feature service, chain, RAG code.
- Next.js frontend (step 4).
- Deployment (deferred; leaning Railway).

## 2. Target layout

```
backend/
  pyproject.toml  uv.lock  .env.example
  alembic.ini  migrations/
  app/
    __init__.py
    main.py        # FastAPI app factory, router include, CORS, exception handlers
    config.py      # pydantic-settings Settings, cached accessor
    db.py          # SQLAlchemy engine, SessionLocal, Base, get_db dependency
    auth.py        # verify Supabase JWT -> get_current_user dependency
    api/
      __init__.py
      health.py    # GET /health
      me.py        # GET /me
  tests/
    conftest.py
    test_health.py
    test_auth.py
docs/
  ... (architecture + this spec)
README.md          # setup + run
```

## 3. Components

- **config.py** — `Settings(BaseSettings)` reads `.env`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY`. Cached via `lru_cache`. `.env.example` committed; `.env` gitignored.
- **db.py** — SQLAlchemy engine from `DATABASE_URL` (Supabase Postgres), `SessionLocal`, declarative `Base`, `get_db()` FastAPI dependency yielding a session.
- **auth.py** — `get_current_user` dependency: reads `Authorization: Bearer <jwt>`, verifies signature with `SUPABASE_JWT_SECRET` (HS256) and audience, returns a small `AuthUser` (id, email). Raises 401 on missing/invalid/expired token.
- **api/health.py** — `GET /health` → `{"status": "ok"}`, 200. No auth.
- **api/me.py** — `GET /me` depends on `get_current_user`, returns the user. Proves the auth path end to end.
- **main.py** — app factory: instantiate FastAPI, add CORS (allow the Next.js origin, configurable), include routers, register exception handlers. Uvicorn entry.
- **migrations/** — Alembic baseline migration runs `CREATE EXTENSION IF NOT EXISTS vector;`. No app tables yet.

## 4. Data flow

1. Client sends request with `Authorization: Bearer <supabase-jwt>`.
2. `get_current_user` verifies the JWT locally against `SUPABASE_JWT_SECRET` (no network call to Supabase).
3. On success the endpoint runs with `AuthUser`; on failure FastAPI returns 401.
4. `get_db` provides a scoped SQLAlchemy session per request (unused by these endpoints beyond a connectivity check, foundation for later services).

## 5. Error handling

- 401 for missing/invalid/expired JWT, consistent JSON shape `{"detail": "..."}`.
- Global exception handler maps uncaught errors to 500 with a safe message (no stack traces to client).
- DB connection failure surfaces clearly at startup / in `/health` if a DB probe is added.

## 6. Testing (TDD, written first)

- `test_health.py` — `GET /health` returns 200 and `{"status":"ok"}`.
- `test_auth.py` — `GET /me`:
  - no header → 401
  - malformed / bad-signature token → 401
  - expired token → 401
  - valid token (signed in-test with the configured secret) → 200 and correct user id/email.
- `conftest.py` — FastAPI `TestClient`, helper to mint a valid/invalid JWT with the test secret, settings overridden for tests.

## 7. Done-when (acceptance)

- `uv sync` installs; `uvicorn app.main:app` boots with no error.
- `GET /health` → 200.
- Alembic migration applies against Supabase Postgres; `pgvector` extension present.
- `GET /me` → user with a valid Supabase JWT, 401 without.
- All tests pass.
- README documents environment setup and run commands.

## 8. Open questions

- Async vs sync SQLAlchemy — default to **sync** for simplicity now; revisit if throughput needs it. (Foundation endpoints don't hit the DB heavily.)
- Supabase JWT: HS256 shared-secret verification (simplest) vs JWKS/RS256. Default HS256 with `SUPABASE_JWT_SECRET`; note JWKS as a later hardening option.
