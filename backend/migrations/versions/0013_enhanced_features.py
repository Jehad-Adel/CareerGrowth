"""enhanced features: granular roadmaps, quiz, video, notifications, offers

Adds micro_points and learning_resources to roadmap_steps, deadline tracking
to job_applications, and creates new tables for quiz attempts/questions,
video summaries, notifications, and offer evaluations.

Revision ID: 0013_enhanced_features
Revises: 0012_applications
Create Date: 2026-07-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0013_enhanced_features'
down_revision: Union[str, Sequence[str], None] = '0012_applications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Roadmap steps: add granular micro-points and learning resources
    op.add_column(
        'roadmap_steps',
        sa.Column('micro_points', sa.JSON(), nullable=False, server_default='[]'),
    )
    op.add_column(
        'roadmap_steps',
        sa.Column('learning_resources', sa.JSON(), nullable=False, server_default='[]'),
    )

    # Job applications: add deadline tracking
    op.add_column(
        'job_applications',
        sa.Column('deadline_at', sa.Date(), nullable=True),
    )
    op.add_column(
        'job_applications',
        sa.Column('next_step', sa.String(length=300), nullable=False, server_default=''),
    )
    op.add_column(
        'job_applications',
        sa.Column('next_step_date', sa.Date(), nullable=True),
    )
    op.add_column(
        'job_applications',
        sa.Column('notified_deadline', sa.Boolean(), nullable=False, server_default='false'),
    )

    # Quiz attempts
    op.create_table(
        'quiz_attempts',
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('source_type', sa.String(length=40), nullable=False, server_default='manual'),
        sa.Column('source_id', sa.Uuid(), nullable=True),
        sa.Column('source_title', sa.String(length=300), nullable=False, server_default=''),
        sa.Column('mastery_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['career_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_quiz_attempts_profile_id'), 'quiz_attempts', ['profile_id'], unique=False,
    )
    op.create_index(
        'ix_quiz_attempts_profile_created', 'quiz_attempts', ['profile_id', 'created_at'], unique=False,
    )

    # Quiz questions
    op.create_table(
        'quiz_questions',
        sa.Column('attempt_id', sa.Uuid(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('correct_answer', sa.Integer(), nullable=False),
        sa.Column('user_answer', sa.Integer(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False, server_default=''),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_quiz_questions_attempt_id'), 'quiz_questions', ['attempt_id'], unique=False,
    )
    op.create_index(
        'ix_quiz_questions_attempt', 'quiz_questions', ['attempt_id'], unique=False,
    )

    # Video summaries
    op.create_table(
        'video_summaries',
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('url', sa.String(length=2000), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('source_type', sa.String(length=20), nullable=False, server_default='youtube'),
        sa.Column('mode', sa.String(length=20), nullable=False, server_default='summary'),
        sa.Column('transcript', sa.Text(), nullable=False, server_default=''),
        sa.Column('summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('key_takeaways', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['career_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_video_summaries_profile_id'), 'video_summaries', ['profile_id'], unique=False,
    )
    op.create_index(
        'ix_video_summaries_profile_created', 'video_summaries', ['profile_id', 'created_at'], unique=False,
    )

    # Notifications
    op.create_table(
        'notifications',
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=40), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False, server_default=''),
        sa.Column('data', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['career_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_notifications_profile_id'), 'notifications', ['profile_id'], unique=False,
    )
    op.create_index(
        'ix_notifications_profile_read', 'notifications', ['profile_id', 'read'], unique=False,
    )

    # Offer evaluations
    op.create_table(
        'offer_evaluations',
        sa.Column('profile_id', sa.Uuid(), nullable=False),
        sa.Column('company', sa.String(length=200), nullable=False),
        sa.Column('role_title', sa.String(length=200), nullable=False),
        sa.Column('offer_details', sa.Text(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('recommendation', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['career_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_offer_evaluations_profile_id'), 'offer_evaluations', ['profile_id'], unique=False,
    )
    op.create_index(
        'ix_offer_evaluations_profile_created', 'offer_evaluations', ['profile_id', 'created_at'], unique=False,
    )

    # RLS policies for new tables
    for table in ('quiz_attempts', 'quiz_questions', 'video_summaries', 'notifications', 'offer_evaluations'):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON public.{table} FROM anon")
        op.execute(f"REVOKE ALL ON public.{table} FROM authenticated")


def downgrade() -> None:
    # Offer evaluations
    op.execute("GRANT ALL ON public.offer_evaluations TO anon")
    op.execute("GRANT ALL ON public.offer_evaluations TO authenticated")
    op.drop_index('ix_offer_evaluations_profile_created', table_name='offer_evaluations')
    op.drop_index(op.f('ix_offer_evaluations_profile_id'), table_name='offer_evaluations')
    op.drop_table('offer_evaluations')

    # Notifications
    op.execute("GRANT ALL ON public.notifications TO anon")
    op.execute("GRANT ALL ON public.notifications TO authenticated")
    op.drop_index('ix_notifications_profile_read', table_name='notifications')
    op.drop_index(op.f('ix_notifications_profile_id'), table_name='notifications')
    op.drop_table('notifications')

    # Video summaries
    op.execute("GRANT ALL ON public.video_summaries TO anon")
    op.execute("GRANT ALL ON public.video_summaries TO authenticated")
    op.drop_index('ix_video_summaries_profile_created', table_name='video_summaries')
    op.drop_index(op.f('ix_video_summaries_profile_id'), table_name='video_summaries')
    op.drop_table('video_summaries')

    # Quiz questions
    op.execute("GRANT ALL ON public.quiz_questions TO anon")
    op.execute("GRANT ALL ON public.quiz_questions TO authenticated")
    op.drop_index('ix_quiz_questions_attempt', table_name='quiz_questions')
    op.drop_index(op.f('ix_quiz_questions_attempt_id'), table_name='quiz_questions')
    op.drop_table('quiz_questions')

    # Quiz attempts
    op.execute("GRANT ALL ON public.quiz_attempts TO anon")
    op.execute("GRANT ALL ON public.quiz_attempts TO authenticated")
    op.drop_index('ix_quiz_attempts_profile_created', table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_profile_id'), table_name='quiz_attempts')
    op.drop_table('quiz_attempts')

    # Job application columns
    op.drop_column('job_applications', 'notified_deadline')
    op.drop_column('job_applications', 'next_step_date')
    op.drop_column('job_applications', 'next_step')
    op.drop_column('job_applications', 'deadline_at')

    # Roadmap step columns
    op.drop_column('roadmap_steps', 'learning_resources')
    op.drop_column('roadmap_steps', 'micro_points')
