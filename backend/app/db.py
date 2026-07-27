from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

Base = declarative_base()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """Turn on FK enforcement for SQLite connections.

    SQLite ships PRAGMA foreign_keys defaulted to OFF, per-connection, and
    SQLAlchemy never issues it for you. Without this listener every
    ondelete="CASCADE" in app/models/* is silently ignored on SQLite: rows
    that should cascade-delete just sit there orphaned, and the test suite
    (which runs entirely against SQLite) would give false confidence that
    cascades work. This is a no-op for every other dialect (e.g. Postgres),
    which enforces FKs natively and doesn't understand this pragma.
    """
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@lru_cache
def get_engine() -> Engine:
    """Build the process-wide engine on first use, not at import time."""
    url = get_settings().database_url
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
        )

    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if not url.startswith("sqlite"):
        # Sized for the Supabase transaction pooler. SQLite's pool
        # implementations reject these arguments, hence the guard.
        kwargs.update(pool_size=5, max_overflow=5, pool_recycle=300)

    return create_engine(url, **kwargs)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
