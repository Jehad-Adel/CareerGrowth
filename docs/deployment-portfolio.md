# Vercel frontend and Railway backend

Keep the screenshot harness local; never publish `.portfolio-harness` or run its fixture service on a public host.

## Current hosting inventory

The existing frontend is `https://career-growth-farm.vercel.app` (HTTP 200), not the older `career-growth-eight` alias. Its previous API `https://careergrowth-production.up.railway.app/health` returns 404. The replacement is service `careergrowth-backend` in the existing Railway project `basira` (`b52507e4-5b7d-4af9-b6f2-3ad97270efa5`), production environment `c590210d-c3f1-4a58-91d0-3b80b87e1dc5`. Public origin: `https://careergrowth-backend-production.up.railway.app`. Validate `/health` before routing the frontend to it.

Railway reports two projects and five services per project for this workspace. Separate services retain independent repository deployments. The complete shared infrastructure graph is maintained in `basira/.railway/railway.ts`; do not apply this repository's standalone reference graph to that shared project, because an incomplete graph proposes deleting sibling resources. Every infrastructure plan must have zero destroys.

The Vercel CLI rejected connecting `Jehad-Adel/CareerGrowth`, despite GitHub CLI WRITE access. Repository owner/app access must be granted to Vercel before native frontend push deployments can be claimed. An existing project and a healthy URL do not establish that source connection.

## Vercel

Connect the actual CareerGrowth repository, with Root Directory `frontend`, Next.js framework, Node 24.x, Install Command `npm ci`, Build Command `npm run build`, Output Directory `.next`. `frontend/vercel.json` pins these commands; the project dashboard must pin the root and production branch. Native Vercel GitHub integration deploys the production branch and creates previews for other branches. Verify the connected repository: an unrelated `zAyman01/career-growth` project is not the `Jehad-Adel/CareerGrowth` checkout.

Set these public environment names in Production and Preview: `NEXT_PUBLIC_API_URL` (public HTTPS Railway API origin, no trailing slash), `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SITE_URL` (canonical frontend origin). Never add database credentials, `GOOGLE_API_KEY`, or a service-role key to Vercel public variables. This app fetches API data from Server Components and server actions, so Vercel functions need outbound access to the public Railway API.

Supabase Auth must use ES256 JWTs, the correct frontend Site URL, and allowed `/auth/callback` redirect URLs. Email confirmation remains enabled. Keep preview auth redirects constrained to the intended Vercel project.

## Railway

New Railway services use `.railway/railway.ts`. `railway.json` is legacy configuration: new services cannot adopt it and existing services stop reading it on 2026-12-01. Install the isolated SDK with `npm ci --prefix .railway`, then locally typecheck it with `npm run typecheck --prefix .railway`. The prepared service is named `backend`, with root directory `backend`, Dockerfile `backend/Dockerfile` relative to the uploaded repository, healthcheck `/health` (60 seconds), and pre-deploy `alembic upgrade head`. The source deliberately omits a GitHub repository because deploys can be uploaded through GitHub Actions using an environment-scoped `RAILWAY_TOKEN`.

Upload from the repository root so Railway root directory supplies the Docker build context. A manual local reproduction is `docker build backend`. Keep the image's existing CMD; no start command override. It expands `PORT`, binds `0.0.0.0`, and execs uvicorn for signal handling. No persistent volume is needed: uploaded PDFs/audio are parsed in memory and not retained.

Provision the external database/auth/AI environment variables before the first production deploy. IaC preserves their platform-managed values rather than embedding credentials. Required names: `DATABASE_URL`, `DIRECT_DATABASE_URL`, `SUPABASE_URL`, `GOOGLE_API_KEY`, `CORS_ORIGINS`. Optional names: `SENTRY_DSN`, `GEMINI_MODEL`, `TEMPERATURE`, `MAX_OUTPUT_TOKENS`. IaC sets `ENVIRONMENT=production`, `DEBUG=false`, `TRUSTED_PROXY_COUNT=1`. Railway injects `PORT`.

`DATABASE_URL` uses a Postgres transaction pooler for runtime traffic; `DIRECT_DATABASE_URL` uses a session pooler for Alembic DDL. On the existing Supabase setup, the direct database hostname is IPv6-only, so the session pooler on port 5432 supports IPv4 migration hosts. Percent-encode reserved characters in the password. Enable pgvector; the migration chain creates the vector extension and deny-by-default RLS. The API connects as table owner, so service-layer profile filters remain the authorization boundary.

`GET /health` runs a database ping and returns HTTP 503 if the database is unavailable. It checks connectivity, not the full schema or AI provider. The pre-deploy migration gate supplies schema readiness. Apply migrations to a fresh pgvector-capable staging database before first release and exercise downgrade/re-upgrade there; never downgrade a populated production database just to test a migration.

The curated corpus is in repository-root `knowledge_base/`, intentionally absent from the Docker context. Run `uv run python -m app.cli.ingest_knowledge` from `backend/` in an authorized checkout after migrations, targeting the chosen database. It uses Gemini embeddings and incurs provider usage; screenshot capture never runs it. Generation, embeddings, interview audio transcription, and several learning features require a valid Google API key and quota.

Set `CORS_ORIGINS` to exact production and approved preview frontend origins. The server forwards a Supabase bearer token; FastAPI verifies its ES256 signature against JWKS. Preserve the nonce CSP and dynamic HTML routes. Validate logged-out protected routes redirect to login, email confirmation works, a token accesses only its own profile, and API outage responses remain readable.

## Automatic release and gates

Use the actual repository's default branch as the production trigger. Existing `.github/workflows/ci.yml` checks backend tests, migration reversibility with pgvector Postgres, frontend lint/typecheck/build, and the dependency audit allowlist. A Railway workflow should wait for that CI to pass, apply reviewed IaC, and upload the repository with `railway up --service backend`. Store `RAILWAY_TOKEN` in the production GitHub environment. Railway login and GitHub App permissions are independent of `gh` authentication. The parent task configures the final workflow and cloud links.

Validate a healthy Railway URL before updating Vercel API configuration. Redeploy Vercel after changing `NEXT_PUBLIC_*`, which are build-time values. For rollback, redeploy the previous known-good code/image and retain a forward-compatible database schema; reverse a production migration only with a reviewed data recovery plan.

Official references, checked 2026-10-12: [Vercel GitHub deployments](https://vercel.com/docs/git/vercel-for-github), [Railway monorepo roots](https://docs.railway.com/deployments/monorepo), [Railway IaC and legacy cutoff](https://docs.railway.com/infrastructure-as-code), [Railway IaC reference](https://docs.railway.com/infrastructure-as-code/reference), [healthchecks](https://docs.railway.com/deployments/healthchecks), [pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command), [GitHub autodeploys](https://docs.railway.com/deployments/github-autodeploys).
