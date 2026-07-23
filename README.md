# CareerFarm

AI career-growth platform. Your professional profile is the single source of truth; every feature (CV analysis, job matching, interview prep, roadmap, chat) reads from and writes back to it, and progress is visualized as a living "farm."

## Documentation

Full engineering docs are in [docs/](docs/README.md):

- [Architecture](docs/architecture.md) — system overview, the integration "spine", data model, build status
- [Backend](docs/backend.md) — FastAPI module map, endpoints, setup, tests
- [Frontend](docs/frontend.md) — Next.js structure, module map, setup
- [Decisions](docs/decisions.md) — key technical choices and trade-offs

## Repo layout

```
backend/    FastAPI service (uv, SQLAlchemy, Alembic)
frontend/   Next.js app (App Router, Tailwind, shadcn/ui)
docs/       Living documentation + design records
.env        Single env file for both apps (gitignored; copy from .env.example)
```

## Stack

- **Backend:** FastAPI (Python 3.11), SQLAlchemy + Alembic, managed with [uv]
- **Data/Auth:** Supabase Postgres + pgvector, Supabase Auth (JWT verified in the API)
- **AI:** Claude (Anthropic), behind the services layer
- **Frontend:** Next.js + React + TypeScript + Tailwind (in `frontend/`)

## Environment

A **single** env file at the repo root serves both apps. Copy it once:

```bash
cp .env.example .env   # fill in Supabase + Anthropic values
```

The backend reads `.env` directly; the frontend loads it via `dotenv-cli` in its npm scripts. Do not create per-app `.env` files.

## Backend setup

Requirements: [uv](https://docs.astral.sh/uv/), a Supabase project.

```bash
cd backend
uv sync
uv run alembic upgrade head  # enables pgvector
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`
Authenticated check: `GET /me` with `Authorization: Bearer <supabase-jwt>` → the user; 401 without.

## Frontend setup

Requirements: Node 20+.

```bash
cd frontend
npm install
npm run dev            # http://localhost:3000
```

## Tests

```bash
cd backend
uv run pytest -v
```
