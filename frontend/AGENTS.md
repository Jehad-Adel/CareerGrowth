<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

<!-- Everything below is hand-written. The block above is tool-managed; keep
     additions outside those markers so a regeneration does not clobber them. -->

Concretely: Next.js **16.2.11**, React **19.2.4**, Tailwind v4, Turbopack by default.

Repo-wide rules live in [../AGENTS.md](../AGENTS.md). What follows is frontend-only.

## Verified Next 16 breaking changes

Each confirmed against the bundled docs, not remembered.

- **`middleware.ts` is renamed `proxy.ts`.** A file named `middleware.ts` is **ignored outright** — no error, no warning. Writing one produces a route guard that never runs while looking correct, leaving every "protected" page public. Ours is `src/proxy.ts` with a named `proxy` export and a `config.matcher`. Confirm it is live: `npm run build` prints `ƒ Proxy (Middleware)`.
- **`proxy` runs on the Node.js runtime.** Edge is unsupported and not configurable.
- **Proxy is an optimistic check, not authorization** — the Next docs say so explicitly. The real boundary is FastAPI verifying the token's ES256 signature. Never gate anything security-critical here alone.
- **Request APIs are async**: `await cookies()`, `await searchParams`, `await params`.

## @supabase/ssr 0.12.3

- **`setAll(cookiesToSet, headers)` takes a second argument** carrying `Cache-Control: private, no-cache, no-store, must-revalidate` and friends. Apply it to the response. Omitting it lets a CDN cache a response that sets auth cookies and serve one user's session to another — a live cross-user leak on Vercel, not a theoretical one.
- **Use `getClaims()`, not `getSession()`.** This project signs with ES256; `getClaims()` verifies locally against JWKS with no per-request network call. `getSession()` returns unverified cookie contents the library's own docs say "must not be trusted".
- Server Components cannot set cookies. The `try/catch` around `cookieStore.set` in `lib/supabase/server.ts` is the documented pattern, not a swallowed bug — `proxy.ts` already performed the write.

## Project conventions

- **Pages never call `serverFetch`.** All data access goes through `src/lib/services.ts`, so an endpoint change stays one change there and nowhere else. Every function is live; no mocks remain.
- `src/lib/api/server.ts` is the only fetch wrapper — Server Components and server actions both use it. There is deliberately **no browser-side API client**: nothing in the app fetches the backend from the client, so adding one would also drag a browser Supabase client back into the bundle.
- **A page's default shape is: static header, then `<Suspense>` around an async body component.** The fallback must be the same skeleton from `components/skeletons.tsx` that the route's `loading.tsx` renders, or a soft navigation and a cold load flash two different layouts.
- **The header is `layout/page-header.tsx`, never a hand-rolled `<h1>`.** `PageHeaderSkeleton` is drawn to match it (eyebrow, `text-2xl sm:text-3xl`, subtitle), so a page that hand-rolls `text-2xl font-bold` renders at a different size and weight than its own `loading.tsx`. Quiz, Video, Offers, and Alerts all shipped that way. The route's container (`mx-auto max-w-3xl`) must match its `loading.tsx` too — `PageHeader` supplies its own bottom margin, so the wrapper needs no `space-y`.
- **The brand is `CareerGrowth`, one word.** The Farm is a *feature* — `/farm`, "My Farm", "The Career Farm" on the landing page, and the "grow your career like a farm" tagline all stay. `docs/superpowers/` and `.superpowers/` keep the old name deliberately: they are dated records, not live docs.
- **Wrap anything the layout also fetches in React's `cache()`** (`getProfile`, `getCvStatus`, `bearer()` in `api/server.ts`). Without it the layout and the page each pay a round trip for the same data on every navigation.
- **`has_cv` is on the profile.** Gate on `profile.hasCv`, never a fresh `/cv/status` call — that endpoint exists for the CV Studio's quota counters.
- Form pending state comes from `SubmitButton` / `PendingFieldset` in `ui/submit-button.tsx`. `useFormStatus` only reports for a form **above** the component reading it, so neither can be the element rendering the `<form>`.
- **`Button` does not support `asChild`.** For a link styled as a button, apply `buttonVariants({ variant, size })` to a `<Link>` — the existing pattern in `landing/closing-cta.tsx` and `dashboard/page.tsx`.
- Auth mutations are **server actions** in `src/app/(auth)/actions.ts`, validated with zod on the server. Client-side validation is convenience only.
- **Wrong password and unknown email must return byte-identical text.** Differentiating them is a user-enumeration oracle. `CREDENTIALS_REJECTED` is the single constant both paths use.
- No `dangerouslySetInnerHTML` anywhere. The codebase has zero; keep it that way — the chat renders LLM output as plain text.
- **The authenticated route list lives in `lib/routes.ts` and nowhere else.** `proxy.ts`, `robots.ts`, and `nav.ts` all read it. They used to keep their own copies, and Applications, Quiz, Video, Offers, and Alerts shipped in the sidebar while the other two still listed the original seven — five routes served their app shell to logged-out visitors and were crawlable. `NavItem["href"]` is typed `ProtectedRoute`, so a sidebar entry missing from the list is a type error. Keep that module dependency-free: `proxy.ts` imports it on the request path.
- **Never `catch` around a call that can `redirect()`.** `serverFetch` answers a 401 with `redirect("/login")`, and `redirect` signals by *throwing* — a plain `catch` turns the bounce into an inline error message while the user sits on a dead page with an expired session. `normalizeApiError` calls `unstable_rethrow` first, so any action that routes its errors through it is safe; anything that catches without it is not.
- **Use `formatDate` from `lib/utils.ts`, never bare `toLocaleDateString()`.** With no arguments that reads the *runtime's* locale: the container's in a Server Component (so every visitor got US `M/D/YYYY` from Railway), and server-then-browser in a Client Component, which is a hydration mismatch.
- **Page `metadata.title` carries no suffix.** The root layout applies `template: "%s · CareerGrowth"`; writing `"Quiz — CareerGrowth"` renders the brand twice.
- Security headers live in `next.config.ts` — **except the CSP**, which is built per request in `lib/csp.ts` and set by `proxy.ts`. Its `connect-src` must include the API URL and the Supabase URL.
- **The CSP carries a per-request nonce, so every route that ships HTML must be dynamic.** The App Router emits inline bootstrap scripts (`self.__next_f.push(...)`); a prerendered page freezes them at build time, where there is no request and no nonce, and the browser blocks all of them — the page renders and then never hydrates, with nothing failing server-side. `/`, `/signup`, and `not-found.tsx` each `await connection()` for exactly this reason. Check after adding a route: `npm run build` must show `ƒ`, not `○`, for anything that returns a document. Only `opengraph-image`, `robots.txt`, and `sitemap.xml` are legitimately static.
- **Never put a CSP back in `next.config.ts`.** A second policy does not replace the proxy's, it is enforced alongside it, and a static `script-src 'self'` re-blocks the nonced scripts.

## Gotchas

- Any route reading cookies or `searchParams` becomes dynamic (`ƒ`). Expected for `/(app)` routes — they render per-user data and must not be prerendered.
- `npm run dev` loads `../.env` through `dotenv-cli`. `dotenv-cli` does **not** fail on a missing file, so on Vercel the script works and every value comes from Vercel env vars instead. It looks broken and is not.
