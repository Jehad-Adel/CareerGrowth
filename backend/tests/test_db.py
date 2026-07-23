from sqlalchemy import text

from app.db import Base, get_db


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_db_yields_and_closes():
    gen = get_db()
    db = next(gen)
    assert db.execute(text("SELECT 1")).scalar() == 1
    gen.close()  # triggers finally: db.close()
