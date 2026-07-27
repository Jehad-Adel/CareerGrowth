"""Guards on the schema that do not need a live database.

The recurring failure mode is silent: `alembic revision --autogenerate` has no
idea RLS exists, so a new table ships readable by the browser's public key
unless someone remembers to add three statements by hand. Three phases in,
that has to be enforced rather than remembered.

These assert the *registry* is complete. Whether the statements actually ran
is verified against Postgres in the deploy check, since only a real database
can answer that.
"""

from pathlib import Path

import app.models  # noqa: F401  — registers every model on Base.metadata
from app.db import Base
from app.security import EXEMPT_TABLES, RLS_TABLES, rls_statements

VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"


def test_every_mapped_table_is_in_the_rls_registry():
    mapped = set(Base.metadata.tables) - EXEMPT_TABLES
    missing = mapped - RLS_TABLES
    assert not missing, (
        f"Tables {sorted(missing)} are mapped but absent from RLS_TABLES. "
        "Add them there and add the statements to their migration — "
        "autogenerate will not do it for you."
    )


def test_the_registry_has_no_phantom_tables():
    mapped = set(Base.metadata.tables) - EXEMPT_TABLES
    stale = RLS_TABLES - mapped
    assert not stale, (
        f"RLS_TABLES lists {sorted(stale)}, which no model maps. "
        "Remove them, or the registry stops being trustworthy."
    )


def test_rls_statements_are_deny_by_default():
    stmts = rls_statements("widgets")
    assert stmts[0] == "ALTER TABLE public.widgets ENABLE ROW LEVEL SECURITY"
    # A permissive policy would undo the whole design.
    assert not any("CREATE POLICY" in s.upper() for s in stmts)
    # FORCE applies RLS to the table owner, which is how the app connects.
    assert not any("FORCE" in s.upper() for s in stmts)
    assert any("FROM anon" in s for s in stmts)
    assert any("FROM authenticated" in s for s in stmts)


def test_migration_revisions_are_unique_and_chained():
    """A duplicated revision id or a broken chain bricks `alembic upgrade`."""
    revisions: dict[str, Path] = {}
    downs: set[str | None] = set()

    for path in VERSIONS.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        rev = next(
            (
                line.split("=", 1)[1].strip().strip("\"'")
                for line in text.splitlines()
                if line.startswith("revision")
            ),
            None,
        )
        assert rev, f"{path.name} declares no revision id"
        assert rev not in revisions, (
            f"Duplicate revision id {rev!r} in {path.name} and "
            f"{revisions[rev].name}"
        )
        revisions[rev] = path

        down = next(
            (
                line.split("=", 1)[1].strip().strip("\"'")
                for line in text.splitlines()
                if line.startswith("down_revision")
            ),
            None,
        )
        downs.add(down)

    assert len(revisions) >= 5

    # Exactly one root (down_revision None) means one linear history, not two
    # heads that alembic would refuse to upgrade.
    roots = [d for d in downs if d in (None, "None")]
    assert len(roots) == 1, f"Expected exactly one root migration, found {roots}"
