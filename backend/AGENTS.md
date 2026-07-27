# Backend — FastAPI + uv

Repo-wide rules live in [../AGENTS.md](../AGENTS.md). What follows is backend-only.

```bash
uv run pytest -q                 # SQLite in memory
uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000
```

**Never `pip install`.** `uv add <pkg>`; `uv.lock` is committed.

## Module map

```
app/main.py       create_app: middleware stack, routers, error handlers
app/config.py     Settings (pydantic-settings), reads the repo-root .env
app/db.py         Base, lazy get_engine/get_sessionmaker, get_db, sqlite FK pragma
app/auth.py       JWKS/ES256 bearer verification -> AuthUser
app/deps.py       DbSession + CurrentProfile — the only way a route gets a profile
app/errors.py     AppError taxonomy + handlers
app/logging.py    structlog JSON + request-id ContextVar
app/limiter.py    GlobalRateLimitMiddleware + slowapi limiter for decorators
app/middleware.py SecurityHeadersMiddleware
app/models/       SQLAlchemy 2 declarative
app/schemas/      Pydantic request/response
app/services/     business logic. Owns authorization by filtering on profile_id
app/api/          routers. Validate, delegate, return. No logic.
```

## Layering

Routes → services → models. Routes never touch a session directly beyond passing `DbSession` through, and never accept a `profile_id` from the client — they depend on `CurrentProfile`, so there is no request shape that addresses another user's data.

From Phase 3, `app/ai/` holds the LangChain chains and **only services import it**.

## Non-obvious invariants

- **Middleware order is asserted by a test.** `add_middleware` makes the last-added outermost; the stack is `CORS → SecurityHeaders → RequestContext → GlobalRateLimit`. Responses built in an inner layer must travel back out through the outer ones to get their headers.
- **Unhandled exceptions are caught inside `RequestContextMiddleware.dispatch`**, not by the registered `Exception` handler — Starlette hoists that handler outside all user middleware, where the request-id ContextVar is already reset and no header can be attached.
- **`GlobalRateLimitMiddleware` exists because slowapi's own middleware is inert here** (see ../AGENTS.md). Per-route limits use `@limiter.limit(...)` decorators, which do work.
- **`quota_service.consume()` runs before a chain invoke, never after.** A rejected call rolls back so repeated over-limit attempts cannot inflate the counter.
- `profile_service.upsert_skills` matches case-insensitively and **only ever raises mastery** — a job-match pass must not demote what the CV established.
- Growth events are append-only. Individual events are never updated or deleted; the whole log cascades away with its profile.
- **`CareerProfile.cv_text` is deferred and `has_cv` is a `column_property`.** `get_current_profile` runs on every authenticated request; loading a multi-thousand-token column to answer a boolean was the cost. Read `profile.has_cv` for the flag — it comes back in the same SELECT. Touching `.cv_text` issues its own query, which is correct for the AI paths and wrong everywhere else.
- **`skills` and `goals` are lazy, deliberately.** They were `selectin`, which added two queries to every authenticated request for collections that one endpoint reads. Query those tables directly (as `farm_service` does) rather than restoring eager loading.

## Migrations

- `migrations/env.py` imports `app.models` (otherwise autogenerate produces empty migrations) and builds the engine directly rather than via `config.set_main_option` (ConfigParser `%` interpolation vs. the percent-encoded password).
- **Autogenerate against Postgres only.** SQLite silently drops expression indexes.
- Always exercise `downgrade` before trusting a migration.
