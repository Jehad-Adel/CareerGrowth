from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logging import get_logger, request_id_var

log = get_logger(__name__)

# These keys are always controlled by the handler, never by caller-supplied
# `extra` data, so a colliding field name can't spoof the response body.
RESERVED_RESPONSE_KEYS = frozenset({"detail", "code", "request_id"})


class AppError(Exception):
    """Base for expected, client-facing failures. Never leaks internals."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, **extra) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra


class QuotaExceeded(AppError):
    status_code = 429
    code = "quota_exceeded"


class NoCvOnProfile(AppError):
    status_code = 409
    code = "no_cv_on_profile"


class InvalidAudioUpload(AppError):
    status_code = 400
    code = "invalid_audio_upload"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        log.warning(
            "app_error",
            code=exc.code,
            path=request.url.path,
            method=request.method,
            extra=exc.extra,
        )
        safe_extra = {k: v for k, v in exc.extra.items() if k not in RESERVED_RESPONSE_KEYS}
        return JSONResponse(
            status_code=exc.status_code,
            content={
                **safe_extra,
                "detail": exc.message,
                "code": exc.code,
                "request_id": request_id_var.get(),
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Last-resort net: in normal operation, unhandled exceptions are
        # caught inside RequestContextMiddleware.dispatch so the request id
        # ContextVar, response header, and CORS headers all stay intact. This
        # handler only fires for exceptions that somehow escape that middleware.
        log.exception(
            "unhandled_exception", path=request.url.path, method=request.method
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "code": "internal_error",
                "request_id": request_id_var.get(),
            },
        )
