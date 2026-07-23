# Get Started

Onboarding for new teammates. From zero to the app running locally in ~5 minutes.

## Prerequisites

| Tool | Why | Install |
|------|-----|---------|
| **Node 20+** | frontend (Next.js) | https://nodejs.org |
| **uv** | backend (Python) | https://docs.astral.sh/uv/ |
| **Git** | version control | https://git-scm.com |
| Supabase project | backend DB + auth (only needed to run the backend live) | https://supabase.com |

> The **frontend runs on its own with mock data** — you don't need the backend or Supabase to see the full UI. Start there if you're doing frontend work.

## 1. Clone and set env

```bash
git clone https://github.com/Jehad-Adel/CareerGrowth.git
cd CareerGrowth
cp .env.example .env
```

There is **one** `.env` at the repo root, shared by both apps. Fill in your Supabase + Anthropic values (only required for the backend). See [.env.example](.env.example).

## 2. Run the frontend (static, no backend needed)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. You'll land on the marketing page; the app lives at `/dashboard`, `/farm`, `/cv`, `/jobs`, `/interview`, `/roadmap`, `/chat`, plus `/login` and `/signup`.

All data is mock data from `src/lib/services.ts`. Nothing calls the backend yet.

## 3. Run the backend (optional, for API work)

```bash
cd backend
uv sync
uv run alembic upgrade head          # needs a real DATABASE_URL in .env
uv run uvicorn app.main:app --reload --port 8000
```

Check: `curl http://localhost:8000/health` → `{"status":"ok"}`. Run tests with `uv run pytest -v`.

## Project map

```
backend/    FastAPI service (uv, SQLAlchemy, Alembic) — see docs/backend.md
frontend/   Next.js app (App Router, Tailwind, shadcn) — see docs/frontend.md
docs/       Architecture, decisions, module docs
.env        Shared env for both apps (gitignored)
HOW-TO-GUIDE.md   Task recipes (add a page, connect to the API, theming, …)
```

## Common commands

| Task | Command (from) |
|------|----------------|
| Run frontend | `npm run dev` (`frontend/`) |
| Build frontend | `npm run build` (`frontend/`) |
| Lint frontend | `npm run lint` (`frontend/`) |
| Run backend | `uv run uvicorn app.main:app --reload` (`backend/`) |
| Backend tests | `uv run pytest -v` (`backend/`) |
| New DB migration | `uv run alembic revision -m "..."` (`backend/`) |

## Where to go next

- Building UI? Read [HOW-TO-GUIDE.md](HOW-TO-GUIDE.md) and [docs/frontend.md](docs/frontend.md).
- Understanding the system? Read [docs/architecture.md](docs/architecture.md).
- Why things are the way they are? Read [docs/decisions.md](docs/decisions.md).
