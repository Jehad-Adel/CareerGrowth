# Explicit Dockerfile rather than leaving Railway's nixpacks to infer a uv
# project. Deterministic, and the same image runs locally.
#
# BUILD CONTEXT IS THE REPO ROOT, not backend/. Railway's `dockerfilePath`
# selects the Dockerfile but does not move the context, so every COPY below
# is written `backend/...`. Build it the same way by hand:
#
#     docker build -f backend/Dockerfile .        # from the repo root
#
# Running it from inside backend/ fails on the first COPY.
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
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./

RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH"

# Run as a non-root user. Nothing here needs to write to the filesystem —
# uploads are parsed in memory and never persisted.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Railway injects $PORT, so the command has to go through a shell to expand
# it — but `exec` hands uvicorn PID 1, so SIGTERM on redeploy reaches the app
# instead of stopping at a shell that ignores it. The bare shell form would
# swallow it and every deploy would end in a 10-second SIGKILL.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
