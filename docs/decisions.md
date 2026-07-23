# Key Decisions & Trade-offs

Condensed record of the choices that shape the project and why. Newest context in [architecture.md](architecture.md); original rationale in the [design specs](superpowers/specs).

| Decision | Chosen | Over | Why / trade-off |
|----------|--------|------|-----------------|
| Integration model | Shared Career Profile + append-only growth-event log ("the spine") | Direct service-to-service calls; full event bus (Kafka) | Features integrate through shared data, not direct coupling. A DB event table gives most of event-sourcing's benefit without the infra. Farm becomes a projection, so it always reflects real progress. |
| Frontend | Real web stack: Next.js + React | Keep the original Streamlit skeleton | Streamlit is fast for demos but weak for multi-user SaaS and the custom animated farm. Next.js gives routing, SSR, and the React ecosystem. Cost: discarded the Streamlit frontend. |
| Frontend framework | Next.js 16 (App Router) | React + Vite SPA; Vue/Nuxt | SaaS standard; SSR + file routing; can host marketing + app. App Router is the current model. |
| Persistence | Supabase Postgres + pgvector | Postgres + separate vector DB; SQLite + Chroma | One datastore for relational data *and* RAG embeddings. Managed infra, ACID, scales. |
| Auth | Supabase Auth; API verifies JWT | Own JWT auth in FastAPI; Clerk/Auth0 | Managed signup/sessions/social login. Backend only verifies the token (HS256, local, no network call). Ties auth to Supabase — acceptable since the DB is already Supabase. |
| LLM provider | Claude (Anthropic), behind one `llm` module | Other providers | Latest Opus/Sonnet; isolated so it's swappable. |
| AI framework | LangChain, hidden behind `services/` | Direct SDK calls everywhere | Keeps RAG/chains structured; routes and frontend never import it, so internals can change (or drop LangChain) without touching callers. |
| Python tooling | uv | Poetry; pip + requirements.txt | Fast, single tool for venv + deps + lockfile. Reproducible builds for CI/Railway. |
| Styling | Tailwind + shadcn/ui | Tailwind only; MUI/Chakra | Own the component code (copy-in), easy to bend into the custom farm look, no heavy dependency. |
| SQLAlchemy mode | Sync | Async | Simpler now; Foundation endpoints don't need async throughput. Revisit if needed. |
| JWT verification | HS256 shared-secret | JWKS/RS256 | Simplest; no key-fetch round-trip. JWKS noted as a later hardening option. |
| Config | Single root `.env` for both apps | Per-app `.env` files | One source of truth. Backend reads it by absolute path; frontend loads it via `dotenv-cli`. |
| Build order | Spine + one AI feature before real UI | Build all features in parallel | Frontend has real profile/farm data to render instead of empty screens. (Frontend *scaffold* was brought forward since it's owned separately.) |

## Deferred / open

- **Deployment** — leaning Vercel (frontend) + Railway (backend). Not set up.
- **Authorization depth** — currently enforced in FastAPI; Postgres RLS as an additional layer is an open question.
- **CV file storage** — Supabase Storage vs. parse-and-discard, decided when CV Studio is built.
- **Live migration** — `alembic upgrade head` needs a provisioned Supabase DB; not yet run against a real instance.
