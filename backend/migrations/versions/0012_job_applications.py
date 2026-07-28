"""job applications tracker

The first table with no AI behind it. `job_match_id` is ON DELETE SET NULL
rather than CASCADE: deleting an old analysis must not delete the record that
you applied for the job.

Revision ID: 0012_applications
Revises: 0011_cover_letters
Create Date: 2026-07-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0012_applications'
down_revision: Union[str, Sequence[str], None] = '0011_cover_letters'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'job_applications',
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('company', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='saved'),
        sa.Column('job_match_id', sa.Uuid(), nullable=True),
        sa.Column('applied_at', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('url', sa.String(length=500), nullable=False, server_default=''),
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
        sa.ForeignKeyConstraint(
            ['job_match_id'], ['job_matches.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_job_applications_profile_id'),
        'job_applications',
        ['profile_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_job_applications_job_match_id'),
        'job_applications',
        ['job_match_id'],
        unique=False,
    )
    op.create_index(
        'ix_job_applications_profile_status',
        'job_applications',
        ['profile_id', 'status'],
        unique=False,
    )

    op.execute("ALTER TABLE public.job_applications ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON public.job_applications FROM anon")
    op.execute("REVOKE ALL ON public.job_applications FROM authenticated")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("GRANT ALL ON public.job_applications TO anon")
    op.execute("GRANT ALL ON public.job_applications TO authenticated")
    op.drop_index('ix_job_applications_profile_status', table_name='job_applications')
    op.drop_index(
        op.f('ix_job_applications_job_match_id'), table_name='job_applications'
    )
    op.drop_index(op.f('ix_job_applications_profile_id'), table_name='job_applications')
    op.drop_table('job_applications')
