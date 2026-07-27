from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api import health, me, profile
from app.config import get_settings
from app.errors import install_error_handlers
from app.limiter import install_rate_limiting
from app.logging import (
    configure_logging,
    get_logger,
    request_id_var,
    sanitize_request_id,
)
from app.middleware import SecurityHeadersMiddleware

log = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a correlation id to every request and echo it back.

    Unhandled exceptions are also caught here rather than left to Starlette's
    `@app.exception_handler(Exception)`. That handler is special-cased onto
    ServerErrorMiddleware, the outermost layer -- outside this middleware. If
    an exception reached it instead, this middleware's `finally` would have
    already reset the request id ContextVar and never set the response
    header, and CORSMiddleware's send-wrapper would never run either. Catching
    here keeps the ContextVar live while the response is built and lets it
    flow back out through CORSMiddleware normally. `install_error_handlers`
    still registers an `Exception` handler as a last-resort net for anything
    that escapes this middleware.
    """

    async def dispatch(self, request: Request, call_next):
        rid = sanitize_request_id(request.headers.get("X-Request-ID"))
        token = request_id_var.set(rid)
        try:
            try:
                response = await call_next(request)
            except Exception:
                log.exception(
                    "unhandled_exception",
                    path=request.url.path,
                    method=request.method,
                )
                response = JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "code": "internal_error",
                        "request_id": rid,
                    },
                )
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_var.reset(token)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.debug)

    app = FastAPI(
        title="CareerFarm API",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    # Middleware add order is reversed at request time: the last-added
    # middleware ends up outermost. Rate limiting is installed first here so
    # GlobalRateLimitMiddleware ends up innermost -- a 429 it returns still
    # flows back out through RequestContextMiddleware, SecurityHeadersMiddleware,
    # and CORSMiddleware, exactly like the 500 path already does. The relative
    # order of those three is unchanged (Task 3 / test_errors.py depend on it).
    install_rate_limiting(app)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        SecurityHeadersMiddleware, production=settings.is_production
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(profile.router)

    install_error_handlers(app)
    return app


app = create_app()
