# CareerFarm — working notes

AI career-growth platform. One canonical `CareerProfile` per user; every feature reads and writes it and emits append-only `growth_events`. The Farm is a **projection** over skills + goals + events, never its own source of truth.

Read [docs/superpowers/plans/2026-07-27-ship-roadmap.md](docs/superpowers/plans/2026-07-27-ship-roadmap.md) for phase sequencing before starting work.

## Layout

```
backend/    FastAPI service (uv, SQLAlchemy 2 sync, Alembic). LangChain chains live in app/ai/
frontend/   Next.js 16 App Router  — see frontend/AGENTS.md, it has its own traps
docs/       Living docs + plans. Update architecture.md and decisions.md as you go
knowledge_base/  Curated JSON corpus (ATS, CV writing, roadmaps). Editorial content,
            committed. Edit a file, then re-run the ingest command below.
.env        Single env file for BOTH apps. Gitignored. Never commit.
```

## Commands

```bash
cd backend  && uv run pytest -q          # full suite
cd backend  && uv run alembic upgrade head
cd backend  && uv run python -m app.cli.ingest_knowledge   # sync knowledge_base/ into pgvector
cd frontend && npm run dev               # loads ../.env via dotenv-cli
cd frontend && npm run build && npm run lint && npx tsc --noEmit
```

- **Never `pip install`.** Use `uv add`. The backend is uv-managed and `uv.lock` is committed.
- Commits: Conventional Commits. **Never add `Co-Authored-By` or any AI attribution.**

## Hard constraints

- **No LangChain import outside `backend/app/ai/`.** Routes import services; only services import chains.
- **Every AI-invoking service method calls `quota_service.consume()` before the chain**, never after — a failed generation still costs tokens.
- **Every service method that reads user data takes `profile_id` and filters on it.** This is the real authorization boundary (see RLS below). Routes never accept a `profile_id` from the client; they depend on `CurrentProfile`.
- **Never return `str(exception)` or a traceback to the client.** Log server-side with the request id.
- **Sync SQLAlchemy only.** No `async def` on anything touching a DB session.
- Every new table: `ENABLE ROW LEVEL SECURITY`, **no** permissive policy, and revoke `anon`/`authenticated`.
- Frontend: pages never call `serverFetch` directly — everything goes through `src/lib/services.ts`.

## Supabase — project-specific facts that cost real time to discover

Project ref `jumsfxzsqvczdevquokk`, region `eu-north-1`.

- **JWTs are ES256 (asymmetric), not HS256.** There is no usable shared secret and no `SUPABASE_JWT_SECRET` anywhere. `app/auth.py` verifies via `PyJWKClient` against `<SUPABASE_URL>/auth/v1/.well-known/jwks.json`, pinned to a single algorithm. Accepting a list of algorithms is how JWT confusion attacks land. Check any project's signing scheme by curling that JWKS URL — it needs no auth.
- **The direct database host `db.<ref>.supabase.co` is IPv6-only.** From an IPv4 network it fails as `could not translate host name`, which reads like a typo. Use the **session pooler** (`aws-0-<region>.pooler.supabase.com:5432`) for Alembic — it is IPv4 and supports session-mode DDL. The **transaction pooler** (`:6543`) serves the running app and cannot run migrations.
- **The database password contains `#`**, so it must be percent-encoded (`%23`) in the URL. That then collides with `alembic.ini`'s ConfigParser, which reads `%` as interpolation syntax. `migrations/env.py` therefore passes the URL straight to `create_engine` and never calls `config.set_main_option`. Do not "simplify" that back.
- **Email confirmation is on** (`mailer_autoconfirm: false`). Signup returns a user with **no session** — never redirect as if logged in. Only the `email` provider is enabled; do not add social buttons.
- **RLS is deny-by-default with zero policies**, and `anon`/`authenticated` grants are revoked. The API connects as `postgres`, the table owner, which **bypasses RLS** — so RLS protects the browser's public key, not the API path. Authorization is the service layer's job.
- **Never use `FORCE ROW LEVEL SECURITY`** while the app connects as the table owner: it would lock the backend out of its own tables.
- **`anon` and `authenticated` are Supabase's roles, not ours.** Every migration from 0003 on revokes their grants, and `REVOKE ... FROM anon` against a role that does not exist is a hard error — so the whole chain used to be unrunnable on a plain Postgres, including CI's own reversibility job. `0001_baseline` now creates both if missing (a no-op on Supabase). Never drop them in a downgrade: on a real project that breaks Auth.

## Backend architecture traps

- **Middleware order is load-bearing.** `add_middleware` makes the *last-added* outermost. Current stack, outermost first: `CORS → SecurityHeaders → RequestContext → GlobalRateLimit`. A 429 or 500 built inside an inner layer must still travel back out through the outer ones to pick up CORS and security headers. Reordering silently breaks that; `tests/test_security.py` asserts the sequence.
- **`@app.exception_handler(Exception)` is hoisted by Starlette to `ServerErrorMiddleware`, the outermost layer** — outside all user middleware, where the request-id ContextVar has already been reset. Unhandled exceptions are therefore caught *inside* `RequestContextMiddleware.dispatch`; the registered handler is only a last-resort net.
- **slowapi's `SlowAPIMiddleware` does not work with FastAPI 0.139.** It needs `route.endpoint`, but `include_router` puts `_IncludedRouter` objects (no such attribute) in `app.routes`, so every route is silently exempt. Replaced by `GlobalRateLimitMiddleware` on the `limits` public API. `@limiter.limit(...)` **decorators** do work — use those for per-route limits.
- `get_engine()` is lazy and `lru_cache`d. Do not build engines at import time.
- **`AppError.extra` may not shadow `detail`/`code`/`request_id`**, and is logged as one nested field — splatting it crashes the handler when a key collides.

## Testing

- Tests run against SQLite in memory and must stay isolated from Supabase — `conftest.py` sets `DATABASE_URL` via `os.environ.setdefault` *before* any app import.
- **SQLite has `PRAGMA foreign_keys` OFF by default.** `app/db.py` registers a connect listener to turn it on, or every `ondelete="CASCADE"` is silently unexercised.
- Fixtures serving `TestClient` need `StaticPool` + `connect_args={"check_same_thread": False}`. TestClient runs on a worker thread, and a fresh connection to `:memory:` gets an empty database with no schema.
- **Run `alembic revision --autogenerate` against Postgres, never SQLite.** Alembic skips expression-based indexes on SQLite with only a `UserWarning`, which would silently ship `skills` without its case-insensitive unique index.

## Deployment — Railway

- **The Docker build context is the repo root, not `backend/`.** `railway.json` sets `dockerfilePath: backend/Dockerfile`, which selects the file but leaves the context where it was. Every `COPY` in the Dockerfile is therefore written `backend/...`, and a plain `docker build .` from inside `backend/` fails on the first one. Build it the way Railway does: `docker build -f backend/Dockerfile .` from the repo root.
- **`.dockerignore` must live next to the *context*, so it belongs at the repo root.** The one that used to sit in `backend/` was silently inert: the whole repo — `frontend/node_modules`, `.git`, and the real `.env` — was being uploaded to the builder on every deploy. Do not re-add one under `backend/`.
- `knowledge_base/` is deliberately not in the image. Ingestion is an operator CLI run against the database from a checkout, never from the deployed container.

## Known, accepted issues

- `npm audit --omit=dev` reports 3 high findings — `sharp`/libvips and `postcss` — all transitive under `next@16.2.11`. `npm audit fix --force` downgrades to `next@9` — do not run it. `next@16.2.12` (current latest) is still inside the advisory range, so there is no upgrade path yet; track the next patch release. CI's `audit` job gates on `frontend/scripts/check-audit.mjs`, which allowlists those advisories **by GHSA id** and fails on anything else — so the job is green today but still blocks on a genuinely new finding. Muting the job wholesale would hide the next real one. When Next patches, the script warns about ids it no longer sees; delete them.
- **`shadcn` is a CLI, so it belongs in `devDependencies`.** It pulls `@modelcontextprotocol/sdk` → `@hono/node-server`, which added a moderate advisory of its own; as a prod dependency that noise lands in the `--omit=dev` audit for a package that never ships to the client.
