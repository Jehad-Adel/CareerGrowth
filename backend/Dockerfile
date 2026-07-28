# Explicit Dockerfile rather than leaving Railway's nixpacks to infer a uv
# project. Deterministic, and the same image runs locally.
#
# BUILD CONTEXT IS backend/, set by the Railway service's Root Directory.
# `dockerfilePath` in railway.json is still resolved from the repo root, which
# is why it reads `backend/Dockerfile` while the context does not. Every COPY
# below is therefore relative to backend/. Build it the same way by hand:
#
#     cd backend && docker build .
#
# Running it from the repo root fails on the first COPY.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# psycopg2-binary ships its own libpq, so no build toolchain is needed.
# curl is here for the container healthcheck only.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Pinned, and must stay >= the uv that wrote uv.lock (0.11.16 at time of
# writing). An older uv cannot read a newer lockfile format and fails the
# build with a version error rather than anything descriptive.
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first: this layer is cached until the lockfile changes, which
# is the difference between a 20-second deploy and a 3-minute one.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH"

# Run as a non-root user. Nothing here needs to write to the filesystem —
# uploads are parsed in memory and never persisted.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# This is the only start path, locally and on Railway — railway.json
# deliberately sets no `startCommand`, because that field would override CMD
# and cannot do either of the two things needed here.
#
# `$PORT` has to expand, which needs a shell: Railway passes `startCommand`
# to argv without one, so a literal `$PORT` reaches uvicorn and it exits with
# "'$PORT' is not a valid integer". And `exec` hands uvicorn PID 1, so
# SIGTERM on redeploy reaches the app instead of stopping at a shell that
# ignores it — but `exec` is only meaningful inside a shell, so putting it in
# `startCommand` instead makes Railway treat it as the executable and fail
# with "The executable `exec` could not be found".
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
