# Frontend

Next.js 16 (App Router) app in `frontend/`. React 19, TypeScript, Tailwind v4, shadcn/ui. Node 20+.

> **Note:** This Next.js version ships breaking changes vs. older docs. Bundled guides live in `frontend/node_modules/next/dist/docs/` — check them before using unfamiliar APIs (see `frontend/AGENTS.md`).

## Module map

```
frontend/
  src/app/
    layout.tsx              # root layout (fonts, metadata)
    page.tsx                # public landing ("Enter the farm")
    (app)/                  # authed area (route group — no URL segment)
      layout.tsx            # sidebar shell
      dashboard/page.tsx    # \
      farm/page.tsx         #  \
      cv/page.tsx           #   } feature routes — currently PageStub placeholders
      jobs/page.tsx         #  /
      interview/page.tsx    # /
      roadmap/page.tsx
      chat/page.tsx
  src/components/
    ui/button.tsx           # shadcn/ui (built on @base-ui/react)
    layout/sidebar.tsx      # nav with active-route highlight (client component)
    layout/page-stub.tsx    # placeholder card used by feature routes
  src/lib/
    nav.ts                  # nav config — the 7 feature routes
    supabase/client.ts      # browser Supabase client (auth)
    api/client.ts           # apiFetch() — calls FastAPI, attaches Supabase JWT
    utils.ts                # cn() class-merge helper
```

## Key pieces

- **`lib/api/client.ts`** — `apiFetch<T>(path, init)` reads the current Supabase session token and sends it as `Authorization: Bearer <jwt>` to `NEXT_PUBLIC_API_URL`. Throws `ApiError(status, detail)` on non-2xx. This is the single door to the backend.
- **`lib/supabase/client.ts`** — `createClient()` returns a browser Supabase client for signup/login/session. Auth UI (login/signup pages) is not built yet — the client is ready for it.
- **`lib/nav.ts` + `components/layout/sidebar.tsx`** — nav is data-driven; add a route by adding a `NavItem`.
- **Route group `(app)`** — wraps authed pages in the sidebar layout without adding an `/app` URL prefix.

## Setup & run

Environment comes from the single root `.env`, loaded via `dotenv-cli` in the npm scripts (`dotenv -e ../.env -- next ...`). Do not add a `frontend/.env`.

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

`NEXT_PUBLIC_*` vars are exposed to the browser; everything else in `.env` stays server-side.

## Build & lint

```bash
npm run build
npm run lint
```

## Known issue

`npm audit` reports high-severity advisories inside Next's bundled `postcss`/`sharp`. The only offered "fix" downgrades Next to a v9 — not viable. Left as-is until Next ships a patched release.
