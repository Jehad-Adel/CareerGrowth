"""cover letters

A fourth job-scoped analysis, sharing the shape of the other three: the job
description that produced it, the chain's verbatim result, and one
denormalised column so a list view and the export path never have to unpack
the JSON.

Revision ID: 0011_cover_letters
Revises: 0010_knowledge
Create Date: 2026-07-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0011_cover_letters'
down_revision: Union[str, Sequence[str], None] = '0010_knowledge'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cover_letters',
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('job_title', sa.String(length=200), nullable=True),
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('result', _JSON, nullable=False),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['profile_id'], ['career_profiles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_cover_letters_profile_id'), 'cover_letters', ['profile_id'], unique=False
    )

    op.execute("ALTER TABLE public.cover_letters ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON public.cover_letters FROM anon")
    op.execute("REVOKE ALL ON public.cover_letters FROM authenticated")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("GRANT ALL ON public.cover_letters TO anon")
    op.execute("GRANT ALL ON public.cover_letters TO authenticated")
    op.drop_index(op.f('ix_cover_letters_profile_id'), table_name='cover_letters')
    op.drop_table('cover_letters')
