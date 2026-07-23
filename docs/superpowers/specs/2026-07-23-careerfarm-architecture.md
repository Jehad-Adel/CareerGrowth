# CareerFarm — System Architecture

**Status:** Approved (2026-07-23)
**Scope:** Platform-wide architecture and build sequencing. Individual features get their own specs.

---

## 1. Product in one line

An AI career-growth platform where a student's professional profile is the single source of truth, and every feature (CV analysis, job matching, interview prep, roadmap, chat) both reads from and writes back to that profile. Progress is visualized as a living "farm." The platform's differentiator is integration: features are not silos, they feed each other.

## 2. Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js + React + TypeScript + Tailwind; Framer Motion / SVG for farm viz | SaaS standard; SSR for marketing/SEO; React ecosystem for the animated farm |
| API | FastAPI (Python), REST/JSON | Async, typed, Pydantic-native, matches existing backend skeleton |
| Application logic | `services/` layer; AI in `chains/` + `rag/` behind it | Routes and frontend never import LangChain; provider/framework swappable |
| Data | Supabase Postgres + **pgvector**; SQLAlchemy + Alembic for app tables | One datastore for relational data *and* RAG embeddings; managed infra |
| Auth | Supabase Auth (GoTrue); FastAPI validates the JWT | Managed signup/sessions/social login; backend only verifies tokens |
| LLM | Claude (Anthropic) via one internal `llm` module | Latest Opus/Sonnet; provider isolated for swap |

**Deliberate calls:**
- LangChain is kept (RAG + chains rely on it) but hidden behind `services/`. If it becomes churn, internals swap without touching callers.
- Supabase provides managed Postgres; Alembic manages our *app* tables against its connection string, Supabase owns the auth schema. Authorization enforced in FastAPI (service-role), not solely RLS.

## 3. Core architecture decision: the spine

Chosen: **Shared Career Profile + append-only growth-event log.**

- One canonical `CareerProfile` per user. Every feature module reads it and writes back to it.
- Features emit **growth events** (`skill_discovered`, `goal_completed`, `cert_added`, ...).
- The **Farm is a read-model projection** computed from skills + goals + growth events — never its own source of truth. This is why the farm always reflects real progress.
- RAG indexes the profile so Chat is grounded in the user's own data.
- Features integrate through *shared data*, not direct service-to-service calls.

Rejected alternatives:
- **Direct service-to-service calls** — coupling grows, silos leak, order-of-call bugs.
- **Full event bus (Kafka)** — overkill now; a `growth_events` table gives most of the benefit. Revisit at scale.

```
                         ┌─────────────────────────────┐
   Next.js frontend  ──► │   FastAPI  (routes / authz)  │
   (app + farm viz)      └──────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │        services layer        │
                         │  cv · job · interview ·       │
                         │  roadmap · profile · farm ·   │
                         │  chat                         │
                         └───┬─────────────┬────────────┘
             reads/writes    │             │  emits growth events
                        ┌────▼────┐   ┌─────▼──────┐
                        │ Career  │   │  growth    │
                        │ Profile │   │  events    │──► Farm projection
                        └────┬────┘   └────────────┘
                             │ indexed
                        ┌────▼────────────────┐
                        │ AI: chains + RAG     │──► Claude
                        │ (pgvector on profile)│
                        └──────────────────────┘
```

**Integration example (end to end):** upload CV → `cv_service` extracts skills + gaps → writes to `CareerProfile` → emits `skill_discovered` → Farm grows plants → gaps feed `roadmap_service` → completing a step emits `goal_completed` → tree grows → `chat_service` answers "what next?" grounded via RAG on the same profile.

## 4. Core data model (the spine)

- `users` — Supabase auth.
- `career_profiles` — 1:1 with user; canonical skills summary, experience, education, target role, level/XP.
- `skills` — name, category, mastery level, source (cv/manual/roadmap). Render as plants/trees.
- `goals` — target, status, progress. Render as growth points.
- `growth_events` — append-only (type, payload, ts). Farm projection reads this.
- `cv_analyses`, `job_matches`, `interview_sessions`, `roadmaps` — per-feature records, all FK to profile.
- `chat_messages` — conversation history.
- `documents` + `embeddings` (pgvector) — RAG corpus = user's own profile + uploaded docs.

**Farm** = read model derived from skills + goals + growth_events. No separate truth.

## 5. Module boundaries

Each service has one purpose, a defined interface, and is independently testable:

- `profile_service` — owns `CareerProfile`; the only writer of canonical profile fields. Others go through it.
- `farm_service` — projects growth_events + skills + goals into farm state. Read-mostly.
- `cv_service`, `job_service`, `interview_service`, `roadmap_service` — feature logic; call AI via `chains/`; emit events.
- `chat_service` — RAG over the profile corpus.
- `chains/` + `rag/` — AI implementation detail; never imported by routes.
- `llm/` — single Claude entry point.

## 6. Build order (each = its own spec → plan → build, vertical slice)

1. **Foundation** — repo layout, FastAPI skeleton, Supabase connect, Alembic, auth-JWT verify, health check, docs scaffolding.
2. **Career Profile + Farm spine** — profile model, skills/goals, growth-event log, Farm projection API.
3. **CV Studio** — first AI feature; feeds profile + farm; proves AI + spine wiring end to end.
4. **Dashboard + Farm viz (frontend)** — Next.js shell, auth flow, dashboard reads profile/farm.
5. **Roadmap** — consumes gaps, writes goals.
6. **Job Match** — reads profile, produces match record.
7. **Interview Coach** — session-based AI practice.
8. **Career Chat** — RAG over everything above; last, needs the corpus to exist.

## 7. Open questions (revisit per sub-project)

- Hosting/deploy target — deferred. Leaning Vercel (frontend) + Railway (FastAPI). Decide before first deploy.
- Whether to enforce authorization via Postgres RLS in addition to FastAPI checks.
- File storage for uploaded CVs (Supabase Storage vs. parse-and-discard).
