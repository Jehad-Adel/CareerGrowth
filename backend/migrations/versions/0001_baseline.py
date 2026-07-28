"""baseline: enable pgvector, and guarantee the roles later migrations revoke

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-23
"""
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

# Supabase provisions these; a plain Postgres has neither. Every migration
# from 0003 on revokes their grants, and `REVOKE ... FROM anon` against a role
# that does not exist is a hard error, not a no-op — so the whole chain was
# unrunnable anywhere except Supabase. That included CI's own "migrations
# apply and reverse cleanly" job, which meant no downgrade had ever actually
# been exercised.
SUPABASE_ROLES = ("anon", "authenticated")


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Postgres has no CREATE ROLE IF NOT EXISTS. On Supabase every one of
    # these raises duplicate_object and is swallowed, so this is a no-op
    # there and the fix everywhere else.
    for role in SUPABASE_ROLES:
        op.execute(
            f"""
            DO $$ BEGIN
                CREATE ROLE {role} NOLOGIN;
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$
            """
        )


def downgrade():
    # The roles are deliberately not dropped. On Supabase they are the
    # platform's, not ours, and dropping them would break Auth for the whole
    # project — a far worse outcome than leaving two unused roles behind on a
    # throwaway test database.
    op.execute("DROP EXTENSION IF EXISTS vector")
