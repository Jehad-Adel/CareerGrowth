"""baseline: enable pgvector

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-23
"""
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS vector")
