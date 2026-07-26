from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logging import get_logger, request_id_var

log = get_logger(__name__)


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


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        log.warning(
            "app_error",
            code=exc.code,
            path=request.url.path,
            method=request.method,
            **exc.extra,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "request_id": request_id_var.get(),
                **exc.extra,
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
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
