import re
import logging
import uuid
from contextvars import ContextVar

import structlog

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def sanitize_request_id(value: str | None) -> str:
    """Accept a client-supplied request id only if it is sane; otherwise mint one.

    Caps length at 64 chars and restricts to [A-Za-z0-9._-] so a client can't
    spoof another request's correlation id or push arbitrary junk into logs.
    """
    if value and _VALID_REQUEST_ID.match(value):
        return value
    return new_request_id()


def _add_request_id(_logger, _method_name, event_dict: dict) -> dict:
    event_dict["request_id"] = request_id_var.get()
    return event_dict


def configure_logging(debug: bool = False) -> None:
    """JSON logs in production, human-readable locally. Idempotent."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
            if debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        # Off because configure_logging() re-runs per create_app() (e.g. in
        # tests that toggle debug); caching would freeze the first process's
        # chain onto loggers that already emitted, ignoring later reconfigures.
        cache_logger_on_first_use=False,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
