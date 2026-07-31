# CareerGrowth

AI career-growth platform. Your professional profile is the single source of truth; every feature (CV analysis, job matching, interview prep, roadmap, chat) reads from and writes back to it, and progress is visualized as a living "farm."

## Start here

- **New teammate?** [GET-STARTED.md](GET-STARTED.md) — running locally in ~5 minutes.
- **Building UI?** [HOW-TO-GUIDE.md](HOW-TO-GUIDE.md) — add a page, connect to the API, theming.

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
- **Data/Auth:** Supabase Postgres + pgvector (768-d vector index), Supabase Auth (ES256 JWT verified in the API)
- **AI Framework:** LangChain Core (Runnable chains), Google Gemini (`gemini-flash-lite-latest`), Pydantic v2 structured outputs for every chain
- **Embeddings:** `gemini-embedding-001` (768-d via Matryoshka truncation, re-normalized for cosine similarity)
- **RAG:** Dual-corpus semantic retrieval — personal documents (`document_chunks`) + curated knowledge base (`knowledge_chunks`, 291 entries across 19 categories)
- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui (in `frontend/`)

## AI Architecture

All LLM interactions follow a strict layered pattern: **Routes → Services → Chains**. No LangChain import exists outside `app/ai/`. Each feature uses a typed Pydantic schema as its structured output, so AI responses are validated at the boundary — no regex parsing, no fragile text extraction.

**11 LangChain runnables**, each built as `PromptTemplate | Gemini.with_structured_output(Schema)`:
- CV Analysis, Job Match, Skill Gap, Resume Optimizer, Cover Letter, Roadmap, Interview, Chat, Quiz, Video Summary, Offer Evaluation

### Deep Hybrid RAG

Before invoking any LLM for **Chat, CV Analysis, Job Matching, Roadmap Generation, or Skill Gap Analysis**, the system performs a dual-corpus retrieval:

1. **Personal corpus** (`document_chunks`) — profile-scoped, contains past analyses, roadmaps, chat history, and uploaded CV text.
2. **Curated knowledge base** (`knowledge_chunks`) — 291 editorial entries across 19 career categories (ATS rules, CV writing guides, skill frameworks, industry benchmarks).

Both corpora share a single 768-d embedding via `gemini-embedding-001`. The question is embedded once; both retrievals run against the same vector. Retrieved chunks are formatted as labelled context blocks and injected into the prompt, grounding the model in verified data and eliminating hallucination.

### Hybrid RAG Coverage

| Feature | Retrieves Context From |
|---------|----------------------|
| Career Chat | Both corpora (existing) |
| CV Analysis | Curated CV best-practices |
| Job Matching | Market data + personal documents |
| Skill Gap | Skill frameworks + personal skills |
| Roadmap | Career path data + user profile |
| Offer Evaluation | Market compensation benchmarks |

## Features

- **CV Analysis** — PDF upload → AI extracts skills, experience, seniority, and actionable improvements.
- **Job Matching** — Structured skill-by-skill comparison with transferable match detection and hiring probability.
- **Skill Gap Analysis** — Ranked missing skills with prerequisites, learning time estimates, and practice projects.
- **Resume Optimizer** — ATS-aware rewrite with before/after compatibility scores.
- **Cover Letter Generator** — Personalized letters grounded in the user's CV and target job.
- **Granular Micro-Roadmaps** — Multi-step career plans with 3–7 micro-points per step and curated learning resources (tutorials, docs, courses, videos, books).
- **Dynamic Quiz Engine** — AI generates multiple-choice questions from any source text, tailored to the user's mastery level (1–5) with post-submission explanations.
- **Video Summarizer / Transcript** — Paste a YouTube URL → fetch transcript → AI summary with key takeaways or raw transcript mode.
- **Speech-to-Text Mock Interviews** — 3 interviewer personas (friendly HR, technical lead, stress interview). Users can respond via voice audio transcribed by Gemini's multimodal model.
- **Career Chat** — Full conversational AI grounded in the user's CV, past analyses, job matches, and curated career guidance via dual-corpus RAG.
- **Application Tracker** — Pipeline management (saved → applied → interviewing → offer → rejected) with deadline tracking.
- **Smart Notifications** — Automatic in-app alerts for approaching deadlines and status changes.
- **Job Offer Evaluator** — Paste a job offer → objective scoring across compensation, growth, work-life, and culture with negotiation tips.
- **XP & Streak System** — 14 event types, 10 level tiers (Seedling → Homesteader), daily streak auto-tracking.

## Environment

A **single** env file at the repo root serves both apps. Copy it once:

```bash
cp .env.example .env   # fill in Supabase + Gemini values
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
