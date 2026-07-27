from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession
from app.logging import get_logger

router = APIRouter(tags=["health"])
log = get_logger(__name__)


@router.get("/health")
def health(db: DbSession):
    """Liveness plus a real database round trip. Railway probes this.

    A probe that returns ok without touching the database reports an outage
    as healthy, which is worse than having no probe at all.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.exception("health_db_check_failed")
        return JSONResponse(
            status_code=503, content={"status": "degraded", "database": "error"}
        )
    return {"status": "ok", "database": "ok"}
