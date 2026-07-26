import pytest
from sqlalchemy import text

from app.config import get_settings
from app.db import Base, get_db, get_engine


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_db_yields_and_closes():
    gen = get_db()
    db = next(gen)
    assert db.execute(text("SELECT 1")).scalar() == 1
    gen.close()  # triggers finally: db.close()


def test_engine_raises_clear_error_when_database_url_missing(monkeypatch):
    get_settings.cache_clear()
    get_engine.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        get_engine()
    get_settings.cache_clear()
    get_engine.cache_clear()


def test_engine_skips_pool_sizing_for_sqlite(monkeypatch):
    get_settings.cache_clear()
    get_engine.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    engine = get_engine()
    assert engine.dialect.name == "sqlite"
    get_settings.cache_clear()
    get_engine.cache_clear()
