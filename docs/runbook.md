# Runbook

Deploy, roll back, and diagnose CareerFarm. Written to be followed at 3am by
someone who did not build it.

- **Frontend** — Vercel, root directory `frontend/`
- **Backend** — Railway, Docker build from `backend/Dockerfile`
- **Database** — Supabase Postgres (`jumsfxzsqvczdevquokk`, `eu-north-1`)

---

## First deploy

### 1. Railway (backend)

Create a service from this repo. `railway.json` selects the Dockerfile
builder; no Nixpacks guessing.

Environment variables:

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | transaction pooler, port **6543** | Serves the running app |
| `DIRECT_DATABASE_URL` | session pooler, port **5432** | Migrations only |
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Load-bearing: the JWKS URL is derived from it |
| `GOOGLE_API_KEY` | Gemini key | |
| `CORS_ORIGINS` | the exact Vercel origin, no trailing slash | Comma-separated for previews |
| `TRUSTED_PROXY_COUNT` | `1` | **Required.** At `0` the rate limiter keys every request to Railway's proxy — one shared bucket for all users |
| `ENVIRONMENT` | `production` | Disables `/docs`, adds HSTS |
| `SENTRY_DSN` | optional | Unset means no error reporting |

There is **no** `SUPABASE_JWT_SECRET` — the project signs with ES256 and the
backend verifies against JWKS. There is no service-role key either; nothing
in this codebase uses one.

### 2. Migrations

**Not run automatically.** Deliberately: two replicas booting at once would
race, and the runtime `DATABASE_URL` points at the transaction pooler, which
cannot run DDL at all.

```bash
railway run --service <service> alembic upgrade head
```

Or locally with `DIRECT_DATABASE_URL` set. Verify:

```bash
uv run alembic current   # expect the newest revision, marked (head)
```

### 2b. Knowledge base corpus

`knowledge_chunks` is populated by a CLI, not by a request and not on boot.
Run it after any migration that touches the table, and after editing anything
under `knowledge_base/`:

```bash
cd backend && uv run python -m app.cli.ingest_knowledge
```

**Run it from a checkout, not from the container.** The Docker build context
is `backend/`, so `knowledge_base/` is not in the image — by design, since the
running API only ever reads the ingested rows out of Postgres. Inside a
container the command exits with `Knowledge base directory not found`.

**The free tier allows 100 *contents* per minute, not 100 requests.** A batch
of 50 texts spends 50 of them, so the full 291-entry corpus takes roughly
three minutes and the command pauses between batches to stay inside the
budget. That wait is normal, not a hang. On a paid tier, raise it:

```bash
cd backend && uv run python -m app.cli.ingest_knowledge --per-minute 1000
```

Re-running is cheap: entries are skipped by content hash, so only what changed
is re-embedded. Each batch commits as it lands, so an interrupted run — Ctrl-C,
a dropped connection, an exhausted quota — keeps everything already embedded
and the next run resumes from there. `--dry-run` parses and reports without
touching the embedding API or the database. Use `--force` only after changing
the embedding model or the entry rendering, where the text is unchanged but
its vector is no longer comparable to the rest.

### 3. Vercel (frontend)

**Root Directory must be set to `frontend` in the Vercel project settings.**
This cannot be done from `vercel.json`; without it the build will not find
`package.json`.

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | the Railway public URL |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | the publishable key (public by design) |
| `NEXT_PUBLIC_SITE_URL` | the Vercel production URL |

`npm run build` is `dotenv -e ../.env -- next build`. `dotenv-cli` does not
fail on a missing file, so on Vercel it loads nothing and every value comes
from the dashboard. It looks broken. It is not.

### 4. Supabase

Authentication → URL Configuration:
- Site URL: the Vercel production URL
- Redirect URLs: `https://<domain>/auth/callback`

Without this, the confirmation-email link bounces to localhost.

### 5. Smoke test

```bash
curl -s https://<railway>/health
```
Expect `{"status":"ok","database":"ok"}`. A `503` with
`"database":"error"` means the app is up but cannot reach Postgres — check
`DATABASE_URL` first.

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<railway>/profile
```
Expect `401`. A `200` here is a critical auth failure — roll back immediately.

Then in a browser: sign up → confirm email → log in → upload a CV → paste a
job description → build a roadmap → complete a step. That path crosses every
service.

---

## Rollback

**Application code.** Railway and Vercel both keep previous deployments;
redeploy the last good one from the dashboard. This is the fast path and is
almost always the right first move.

**Database.** Every migration has a tested `downgrade`; CI reverses the whole
chain on each run. To step back one:

```bash
uv run alembic downgrade -1
```

Roll the *code* back first, then the schema, never the reverse — a new schema
with old code is usually survivable, old schema with new code is not.

**Rolling back a migration destroys the data in the tables it drops.** There
is no undo. Take a Supabase backup first if the data matters.

---

## Diagnosis

Every response carries `X-Request-ID`, and every log line carries the same id
under `request_id`. Get the header from the user, grep the Railway logs for
it, and you have the exact request.

Logs are JSON. Useful fields: `event`, `level`, `request_id`, `path`.

| Symptom | Likely cause |
|---|---|
| Every request 401s | Supabase rotated signing keys, or `SUPABASE_URL` is wrong so JWKS 404s |
| `could not translate host name` | Using the direct DB host, which is IPv6-only. Use a pooler host |
| `invalid interpolation syntax` from Alembic | A `%` in the password hitting ConfigParser. `migrations/env.py` avoids this — check nothing reintroduced `config.set_main_option` |
| One user's rate limit affects everyone | `TRUSTED_PROXY_COUNT` is unset or `0` behind Railway's proxy |
| Browser shows "Failed to fetch" on a 429 or 500 | A middleware returned early and skipped CORS. Middleware order is asserted by `tests/test_security.py` |
| Chat returns nothing relevant | Corpus empty. `GET /chat` reports `corpus_chunks`; it fills from CV/job/roadmap runs |
| Chat is slow and the DB is hot | The HNSW index is missing. `tests/test_rag_postgres.py::test_the_hnsw_index_exists` checks this |
| 429s on AI endpoints | Working as designed. Daily budgets are in `quota_service.DAILY_LIMITS` |

**Nothing is ever written to disk.** Uploaded CVs are parsed in memory and
discarded; only extracted text reaches the database. If you are looking for
an uploaded file, there is not one.

---

## Incident response

1. **Assess.** `/health` first: is it the app, the database, or Gemini?
2. **Roll back before debugging** if users are affected. Diagnose from logs
   afterwards, not from production.
3. **Credential compromise.** Rotate in the Supabase dashboard, then update
   Railway and redeploy. Note that the database password grants full access
   and **bypasses RLS** — rotating it is urgent in a way the publishable key
   is not.
4. **Runaway Gemini spend.** Lower the values in
   `quota_service.DAILY_LIMITS` and redeploy; they take effect on the next
   request. To stop all AI immediately, unset `GOOGLE_API_KEY` — AI endpoints
   will 502 while the rest of the app keeps working.

---

## Security model, in one paragraph

Every table has RLS enabled with **zero policies** and `anon`/`authenticated`
revoked. The API connects as the table owner and therefore *bypasses* RLS —
so RLS is not what protects the API. Authorization is the service layer's
job: every method filters on `profile_id`, and routes never accept one from
the client. RLS exists so the browser's publishable key, which is public by
construction, can read nothing if it leaks. `app/security.py` lists the tables
this applies to, and `tests/test_migrations.py` fails the build if a new table
is not in it.

Verify on the live database:

```sql
SELECT c.relname, c.relrowsecurity, count(p.polname) AS policies
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
LEFT JOIN pg_policy p ON p.polrelid = c.oid
WHERE c.relkind = 'r'
GROUP BY 1, 2 ORDER BY 1;
```

Expect `relrowsecurity = true` and `policies = 0` for every application
table. A policy appearing is a regression, not an improvement.
