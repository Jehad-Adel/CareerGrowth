# CareerFarm

AI career-growth platform. Your professional profile is the single source of truth; every feature (CV analysis, job matching, interview prep, roadmap, chat) reads from and writes back to it, and progress is visualized as a living "farm."

Architecture and design decisions live in [docs/superpowers/specs](docs/superpowers/specs) and [docs/superpowers/plans](docs/superpowers/plans).

## Stack

- **Backend:** FastAPI (Python 3.11), SQLAlchemy + Alembic, managed with [uv]
- **Data/Auth:** Supabase Postgres + pgvector, Supabase Auth (JWT verified in the API)
- **AI:** Claude (Anthropic), behind the services layer
- **Frontend:** Next.js + React + TypeScript (added in a later sub-project)

## Backend setup

Requirements: [uv](https://docs.astral.sh/uv/), a Supabase project.

```bash
cd backend
cp .env.example .env         # fill in DATABASE_URL, SUPABASE_JWT_SECRET, ...
uv sync
uv run alembic upgrade head  # enables pgvector
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`

Authenticated check: `GET /me` with `Authorization: Bearer <supabase-jwt>` → the user; 401 without.

## Tests

```bash
cd backend
uv run pytest -v
```
