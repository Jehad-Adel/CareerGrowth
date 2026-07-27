"""Registry of tables that must be deny-by-default in Postgres.

Every application table gets `ENABLE ROW LEVEL SECURITY` with **no** policy,
and `anon`/`authenticated` revoked. The API connects as the table owner and
bypasses RLS, so this does not protect the API path — per-`profile_id`
filtering in the service layer does that. This exists so the browser's public
Supabase key, which is public by construction, can read nothing if it leaks.

Adding a table without adding it here fails `tests/test_migrations.py`, which
is the point: `alembic revision --autogenerate` has no idea RLS exists and
will happily ship a readable table.
"""

RLS_TABLES: frozenset[str] = frozenset(
    {
        "career_profiles",
        "skills",
        "goals",
        "growth_events",
        "ai_usage",
        "cv_analyses",
        "job_matches",
        "skill_gap_analyses",
        "resume_optimizations",
        "roadmaps",
        "roadmap_steps",
    }
)

# Alembic's own bookkeeping. Never holds application data.
EXEMPT_TABLES: frozenset[str] = frozenset({"alembic_version"})


def rls_statements(table: str) -> list[str]:
    """SQL a migration should run for a newly created table."""
    return [
        f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY",
        f"REVOKE ALL ON public.{table} FROM anon",
        f"REVOKE ALL ON public.{table} FROM authenticated",
    ]
