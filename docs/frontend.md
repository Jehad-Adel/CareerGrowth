# Frontend

Next.js 16 (App Router) app in `frontend/`. React 19, TypeScript, Tailwind v4, shadcn/ui. Node 20+.

**Current state:** the full UI is built and **static** — every page renders real, designed screens from mock data. Nothing calls the backend yet; the data layer is shaped so pages swap to the live API without UI changes.

> **Note:** This Next.js version ships breaking changes vs. older docs. Bundled guides live in `frontend/node_modules/next/dist/docs/` — check them before using unfamiliar APIs (see `frontend/AGENTS.md`).

## Routes

| Route | Page | Notes |
|-------|------|-------|
| `/` | Landing | Marketing hero with the growth metaphor |
| `/login`, `/signup` | Auth | Static forms, Supabase-ready |
| `/dashboard` | Dashboard | Stats, farm preview, goals, activity |
| `/farm` | Career Farm | **Signature** — skills as plants in category beds |
| `/cv` | CV Studio | Upload + score rings + section feedback |
| `/jobs` | Job Match | Paste JD + fit ring + gaps |
| `/interview` | Interview Coach | Question cards + answer boxes |
| `/roadmap` | Roadmap | Timeline of steps to target role |
| `/chat` | Career Chat | Chat UI grounded in the profile |

`(app)` and `(auth)` are route groups — they attach a shared layout without adding a URL segment.

## Module map

```
frontend/src/
  app/
    layout.tsx              # root: fonts (Fraunces + Geist), metadata
    globals.css             # design tokens (the farm palette), light + dark
    page.tsx                # landing
    (auth)/                 # login, signup + centered auth layout
    (app)/
      layout.tsx            # sidebar + topbar shell (fetches profile)
      dashboard|farm|cv|jobs|interview|roadmap/page.tsx
      chat/page.tsx
  components/
    farm/plant.tsx          # SVG plant by growth stage (seed→tree)
    farm/farm-plot.tsx      # beds grouped by category; FarmPreview for dashboard
    layout/sidebar.tsx      # nav (active highlight)
    layout/topbar.tsx       # search, streak, level/XP, avatar
    layout/page-header.tsx  # eyebrow + title + subtitle
    layout/stat.tsx         # stat tile
    ui/                     # shadcn/ui + score-ring.tsx
  lib/
    services.ts             # data access — mock now, swap to apiFetch later
    mock/data.ts            # sample profile, skills, goals, cv, jobs, …
    growth.ts               # masteryToStage() + stage labels
    nav.ts                  # sidebar nav config
    api/client.ts           # apiFetch() — attaches Supabase JWT
    supabase/client.ts      # browser Supabase client (auth)
    utils.ts                # cn()
  types/index.ts            # domain types (mirror the backend model)
```

## Design system

A deliberate "cultivated / almanac" identity, not default SaaS:

- **Palette** (CSS tokens in `globals.css`): sage-white paper, deep pine ink, **sprout** green (primary), **soil** brown, **harvest** amber (XP), pale sage mist. Brand extras exposed as `text-sprout` / `text-soil` / `text-harvest` / `text-sky`. All tokens have light + dark values.
- **Type:** Fraunces (organic serif) for display headings via `font-heading` (auto-applied to `h1/h2/h3`); Geist Sans body; Geist Mono for stats/labels via `font-mono`.
- **Signature:** the Career Farm — skills rendered as SVG plants whose growth stage reflects mastery (`plant.tsx` + `growth.ts`).

See [HOW-TO-GUIDE.md](../HOW-TO-GUIDE.md) for using tokens and adding pages.

## Data layer

Pages call `src/lib/services.ts`. Each function returns mock data today and maps 1:1 to a future backend endpoint (e.g. `getDashboard()` → `GET /dashboard`). To go live, replace a function's body with `apiFetch<T>(path)` — signatures and pages stay identical. `apiFetch` sends the Supabase JWT automatically.

## Setup & run

Environment comes from the single root `.env`, loaded via `dotenv-cli` in the npm scripts. Do not add a `frontend/.env`.

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000  (works with no backend)
```

## Build & lint

```bash
npm run build      # type-checks + prerenders every route
npm run lint
```

## Known issue

`npm audit` reports high-severity advisories inside Next's bundled `postcss`/`sharp`. The only offered "fix" downgrades Next to v9 — not viable. Left as-is until Next ships a patched release.
