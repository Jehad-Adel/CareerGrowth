# How-To Guide

Task recipes for working on CareerFarm. Mostly frontend, since that's where most day-to-day work is right now. New here? Start with [GET-STARTED.md](GET-STARTED.md).

## Contents

- [Run only the frontend](#run-only-the-frontend)
- [Add a new feature page](#add-a-new-feature-page)
- [Use the design tokens (the farm palette)](#use-the-design-tokens-the-farm-palette)
- [Add a shadcn/ui component](#add-a-shadcnui-component)
- [Connect a page to the real backend](#connect-a-page-to-the-real-backend)
- [Add or change a skill / plant](#add-or-change-a-skill--plant)
- [Dark mode](#dark-mode)
- [Build and checks](#build-and-checks)

---

## Run only the frontend

The UI is fully static (mock data), so you never need the backend for frontend work.

```bash
cd frontend
npm run dev        # http://localhost:3000
```

---

## Add a new feature page

Routes are folders under `frontend/src/app`. The authed app lives in the `(app)` route group (which adds the sidebar + topbar shell without an `/app` URL prefix).

1. Create the page:

```tsx
// frontend/src/app/(app)/certificates/page.tsx
import { PageHeader } from "@/components/layout/page-header";

export default function CertificatesPage() {
  return (
    <>
      <PageHeader eyebrow="Certificates" title="Your certificates" />
      {/* your UI */}
    </>
  );
}
```

2. Add it to the sidebar nav:

```ts
// frontend/src/lib/nav.ts
import { Award } from "lucide-react";
// ...
export const navItems: NavItem[] = [
  // ...existing items
  { href: "/certificates", label: "Certificates", icon: Award },
];
```

That's it — the route and nav link now work.

---

## Use the design tokens (the farm palette)

Never hard-code colors. Use the tokens (defined in `frontend/src/app/globals.css`). They adapt to light/dark automatically.

| Use | Class |
|-----|-------|
| Page background / text | `bg-background` / `text-foreground` |
| Card surface | `bg-card` + `border` |
| Primary (sprout green) | `bg-primary` `text-primary` |
| Muted text | `text-muted-foreground` |
| Brand extras | `text-sprout` `text-soil` `text-harvest` `text-sky` |
| Display headings | `font-heading` (Fraunces) — `h1/h2/h3` get it automatically |
| Data / labels / XP | `font-mono` (Geist Mono) |

Example stat label: `<p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">`.

The **farm plants** are `src/components/farm/plant.tsx`; growth thresholds live in `src/lib/growth.ts`.

---

## Add a shadcn/ui component

```bash
cd frontend
npx shadcn@latest add dialog dropdown-menu   # example
```

Components land in `src/components/ui/` and already inherit the farm theme. Import from `@/components/ui/<name>`.

---

## Connect a page to the real backend

Every page reads data through `frontend/src/lib/services.ts`. Right now each function returns mock data. To go live, swap the body for the matching `apiFetch` call — **the function signature and the page stay the same.**

```ts
// src/lib/services.ts — before (mock)
export const getDashboard = (): Promise<DashboardData> =>
  wait({ profile: mock.profile, skills: mock.skills, /* ... */ });

// after (live) — apiFetch attaches the Supabase JWT automatically
import { apiFetch } from "@/lib/api/client";
export const getDashboard = (): Promise<DashboardData> =>
  apiFetch<DashboardData>("/dashboard");
```

`apiFetch` (`src/lib/api/client.ts`) reads the current Supabase session token and sends it as `Authorization: Bearer <jwt>` to `NEXT_PUBLIC_API_URL`. Set that (and the Supabase keys) in the root `.env`.

Do this one function at a time — pages don't change.

---

## Add or change a skill / plant

Skills drive the farm. A skill's `mastery` (0–100) decides its plant stage via `masteryToStage` (`src/lib/growth.ts`): `seed` <20, `sprout` 20–49, `growing` 50–79, `tree` 80+.

To add a mock skill, edit `src/lib/mock/data.ts`:

```ts
{ id: "s13", name: "Kubernetes", category: "DevOps", mastery: 12, source: "roadmap" },
```

It appears automatically in the DevOps bed on `/farm` and in the dashboard preview. Categories and their order live in `CATEGORY_ORDER` in `src/components/farm/farm-plot.tsx`.

---

## Dark mode

All tokens have light and dark values. To enable dark mode, add the `dark` class to `<html>` (e.g. via a theme toggle). No component changes needed. There's no toggle in the UI yet — adding one is a good starter task (`next-themes` is the usual choice).

---

## Build and checks

```bash
cd frontend
npm run build      # type-checks + prerenders every route
npm run lint       # eslint
```

Both must pass before you push. `npm run build` is the fastest way to catch type errors across the whole app.
