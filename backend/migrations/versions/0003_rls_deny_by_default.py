"""Enable RLS on every application table, with no permissive policy.

Why deny-by-default rather than user-scoped policies:

The API connects as `postgres`, which owns these tables and therefore
bypasses RLS. Writing per-user policies would protect nothing on that path —
which is why per-profile_id filtering in the service layer is a hard project
constraint, not a nicety.

RLS earns its place against a different threat. The browser must hold a
Supabase publishable/anon key for Auth to work, and that key is public by
construction. Enabling RLS with zero policies means it can read and write
nothing. Adding any permissive policy would weaken exactly the property this
migration exists to establish.

The REVOKE is belt-and-braces: RLS already blocks the rows, and revoking the
grants blocks the statement before it gets that far. This project's frontend
uses Supabase solely for authentication and reaches all data through the
FastAPI service, so nothing legitimate needs these grants. If a later phase
ever wants Realtime or direct PostgREST access on a table, that is a
deliberate, separate migration.

Note: FORCE ROW LEVEL SECURITY is deliberately NOT used. It applies RLS to
the table owner too, which — since the app connects as the owner — would lock
the backend out of its own tables. Revisit only alongside a dedicated
non-owner application role.

Revision ID: 0003_rls_deny_by_default
Revises: 0002_core_schema
"""
from alembic import op

revision = "0003_rls_deny_by_default"
down_revision = "0002_core_schema"
branch_labels = None
depends_on = None

TABLES = ["career_profiles", "skills", "goals", "growth_events", "ai_usage"]
PUBLIC_ROLES = ["anon", "authenticated"]


def upgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        for role in PUBLIC_ROLES:
            op.execute(f"REVOKE ALL ON public.{table} FROM {role}")


def downgrade():
    for table in TABLES:
        for role in PUBLIC_ROLES:
            op.execute(f"GRANT ALL ON public.{table} TO {role}")
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
