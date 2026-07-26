import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from limits import RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings


def client_key(request: Request) -> str:
    """Real client IP, trusting X-Forwarded-For only as far as configured.

    `X-Forwarded-For` is entirely client-supplied unless we know exactly how
    many reverse proxies sit in front of us and trust each of them to append
    (never rewrite) an entry. `settings.trusted_proxy_count` is that number.

    - 0 (default; correct for local dev and any deployment without a proxy):
      the header is ignored outright and the socket peer address is used.
    - N > 0: take the entry N positions from the *right-hand* end of the
      header -- the ones appended by proxies we actually control -- never
      the leftmost, which is whatever the original caller claimed. If the
      header has fewer than N entries, fall back to the socket peer rather
      than guessing.
    """
    count = get_settings().trusted_proxy_count
    if count > 0:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            if len(parts) >= count:
                return parts[-count]
    return _socket_peer(request)


def _socket_peer(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# Per-route decorator limiter -- Phase 3 will put @limiter.limit("5/minute")
# on the CV upload route. The decorator path works standalone (it checks
# limits inline in the wrapped endpoint) and does not depend on
# SlowAPIMiddleware's route-table walk, so it is unaffected by the bug below.
limiter = Limiter(key_func=client_key)

# Global backstop -- a 120/minute ceiling across every request, decorated or
# not. Built directly on `limits` (already a transitive dependency of
# slowapi) via its public API only, because SlowAPIMiddleware silently
# no-ops on any route registered through app.include_router() on this
# FastAPI version: it walks app.routes looking for an `endpoint` attribute,
# but include_router() produces `_IncludedRouter` entries that don't have
# one, so `_should_exempt` short-circuits true for every business route.
GLOBAL_RATE_LIMIT = RateLimitItemPerMinute(120)
_global_storage = MemoryStorage()
_global_limiter = MovingWindowRateLimiter(_global_storage)


def reset_rate_limit_state() -> None:
    """Clear every rate-limit counter.

    Both limiters above are backed by module-level, process-wide in-memory
    storage shared by every app `create_app()` builds. Call this before and
    after each test, or hits accumulate across tests and the suite becomes
    order-dependent.
    """
    _global_storage.reset()
    limiter.reset()


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """120/minute backstop, keyed by client_key.

    Installed innermost (added first in create_app), so a 429 still travels
    back out through RequestContextMiddleware, SecurityHeadersMiddleware, and
    CORSMiddleware and picks up their headers. Outermost would be marginally
    cheaper, but the rejection would then carry no Access-Control-Allow-Origin
    and a browser could not read the body it is meant to act on. Rejection
    still happens before the route handler and any database work.
    """

    async def dispatch(self, request: Request, call_next):
        key = client_key(request)
        if not _global_limiter.hit(GLOBAL_RATE_LIMIT, key):
            stats = _global_limiter.get_window_stats(GLOBAL_RATE_LIMIT, key)
            retry_after = max(1, int(stats.reset_time - time.time()))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "code": "rate_limited"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


def install_rate_limiting(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(GlobalRateLimitMiddleware)
