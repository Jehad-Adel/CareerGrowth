# Frontend

Next.js 16 (App Router) app in `frontend/`. React 19, TypeScript, Tailwind v4, shadcn/ui. Node 20+.

**Current state:** every page is live against the FastAPI backend. The mock data layer has been deleted. Each route streams: a static header paints immediately, and the data-dependent body arrives behind a `Suspense` boundary whose fallback is the same skeleton the route's `loading.tsx` uses.

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
      layout.tsx            # sidebar + streamed topbar shell
      */page.tsx            # one per feature, header + <Suspense> body
      */loading.tsx         # route skeleton, shown during navigation
      */actions.ts          # server actions (mutations)
  components/
    skeletons.tsx           # every loading placeholder, shaped like its target
    farm/plant.tsx          # SVG plant by growth stage (seed→tree)
    farm/farm-plot.tsx      # beds grouped by category; FarmPreview for dashboard
    chat/conversation.tsx   # transcript + composer, optimistic on send
    layout/sidebar.tsx      # nav (active highlight, collapse pref in a cookie)
    layout/topbar.tsx       # streak, level/XP, avatar, sign out
    layout/page-header.tsx  # eyebrow + title + subtitle
    layout/stat.tsx         # stat tile
    ui/                     # shadcn/ui + score-ring.tsx + submit-button.tsx
  lib/
    services.ts             # data access — one function per endpoint
    growth.ts               # growth-stage labels
    nav.ts                  # sidebar nav config
    api/server.ts           # serverFetch() — attaches the Supabase JWT
    api/error.ts            # ApiError
    supabase/server.ts      # server Supabase client (cookies)
    utils.ts                # cn()
  types/index.ts            # shared UI types (Profile, GrowthStage)
```

## Design system

A deliberate "cultivated / almanac" identity, not default SaaS:

- **Palette** (CSS tokens in `globals.css`): sage-white paper, deep pine ink, **sprout** green (primary), **soil** brown, **harvest** amber (XP), pale sage mist. Brand extras exposed as `text-sprout` / `text-soil` / `text-harvest` / `text-sky`. All tokens have light + dark values.
- **Type:** Fraunces (organic serif) for display headings via `font-heading` (auto-applied to `h1/h2/h3`); Geist Sans body; Geist Mono for stats/labels via `font-mono`.
- **Signature:** the Career Farm — skills rendered as SVG plants whose growth stage reflects mastery (`plant.tsx` + `growth.ts`).

See [HOW-TO-GUIDE.md](../HOW-TO-GUIDE.md) for using tokens and adding pages.

## Data layer

Pages call `src/lib/services.ts`, never `serverFetch` directly. Each function maps 1:1 to a backend endpoint (e.g. `getDashboardData()` → `GET /dashboard`) and returns the wire shape, so an endpoint change stays a change in one file.

`getProfile()` and `getCvStatus()` are wrapped in React's `cache()`. The app layout renders the profile on every page while pages read it too; without deduplication that is two round trips per navigation. `has_cv` rides along on the profile, so Jobs, Roadmap, Interview, and Chat gate on it instead of each calling `/cv/status`.

The bearer-token lookup in `api/server.ts` is cached the same way — a page fetching three endpoints in parallel builds one Supabase client, not three.

## Loading states

Three layers, deliberately:

1. **`loading.tsx` per route** — instant feedback on navigation, before the server has sent anything.
2. **`Suspense` inside each page** — the header and any static shell paint first; only the data-dependent body waits. Fallbacks come from `components/skeletons.tsx`, which the route's `loading.tsx` also uses, so both paths show the same shape.
3. **Inline pending state** — `SubmitButton` and `PendingFieldset` (`ui/submit-button.tsx`) read `useFormStatus` to swap in a spinner and freeze the form's inputs mid-request. Chat goes further: `useOptimistic` puts the question on screen immediately, with a typing indicator until the answer lands.

Skeletons mirror the real component's box model — same paddings, same grid, same heights — so streamed content never shifts the layout.

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
