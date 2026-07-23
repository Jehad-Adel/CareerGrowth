# CareerFarm Documentation

Living documentation for engineers working on CareerFarm. Kept in sync with the code — if you change behavior, update the relevant page here in the same PR.

## Contents

| Doc | What's in it |
|-----|--------------|
| [architecture.md](architecture.md) | System overview, the integration "spine", data model, build status |
| [backend.md](backend.md) | FastAPI backend: module map, endpoints, setup, tests |
| [frontend.md](frontend.md) | Next.js frontend: structure, module map, setup |
| [decisions.md](decisions.md) | Key technical decisions and trade-offs |

## Design records (point-in-time, provenance)

The `superpowers/` folder holds the original design specs and implementation plans. They are historical records of *how* decisions were made; the docs above are the authoritative, current view.

- [specs/](superpowers/specs) — architecture + sub-project design specs
- [plans/](superpowers/plans) — step-by-step implementation plans

## Quick start

See the [root README](../README.md) for setup. In short: one root `.env`, backend via `uv`, frontend via `npm`.
