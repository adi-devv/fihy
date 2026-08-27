"""confirmation moves to photo evidence, and the fix-date poll

Confirming a report used to mean any three people supporting it. It now means
two people other than the reporter turning up *with a photo*, and the moment
that happens is stored, because the contributions window counts from it and a
derived timestamp could not survive a withdrawal.

Revision ID: 0005_fix_dates
Revises: 0004_index_filters
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005_fix_dates'
down_revision: str | None = '0004_index_filters'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONFIRMS = 2


def upgrade() -> None:
    op.create_table(
        'fix_dates',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('issue_id', sa.String(length=32), nullable=False),
        sa.Column('created_by', sa.String(length=32), nullable=False),
        sa.Column('fix_on', sa.Date(), nullable=False),
        sa.Column('vote_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_id', 'created_by', name='uq_fix_dates_issue_creator'),
        sa.UniqueConstraint('issue_id', 'fix_on', name='uq_fix_dates_issue_day'),
    )
    op.create_index('ix_fix_dates_created_by', 'fix_dates', ['created_by'])

    op.create_table(
        'fix_date_votes',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('fix_date_id', sa.String(length=32), nullable=False),
        sa.Column('issue_id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['fix_date_id'], ['fix_dates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fix_date_id', 'user_id', name='uq_fix_date_votes_date_user'),
    )
    op.create_index('ix_fix_date_votes_user_issue', 'fix_date_votes', ['user_id', 'issue_id'])

    # Autogenerate emits photo_support_count as a bare NOT NULL, which cannot be
    # applied to a table that already has rows.
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('photo_support_count', sa.Integer(), nullable=False, server_default=sa.text('0'))
        )
        batch_op.add_column(sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.alter_column('photo_support_count', server_default=None)

    op.execute(
        """
        UPDATE issues SET photo_support_count = (
            SELECT COUNT(*) FROM supports s
             WHERE s.issue_id = issues.id
               AND s.user_id <> issues.reporter_id
               AND EXISTS (SELECT 1 FROM issue_photos p WHERE p.support_id = s.id)
        )
        """
    )

    # The moment a report crossed the bar is the created_at of the support that
    # crossed it, which needs a row walk rather than an aggregate.
    bind = op.get_bind()
    qualifying = bind.execute(
        sa.text(
            """
            SELECT s.issue_id, s.created_at
              FROM supports s
              JOIN issues i ON i.id = s.issue_id
             WHERE s.user_id <> i.reporter_id
               AND EXISTS (SELECT 1 FROM issue_photos p WHERE p.support_id = s.id)
             ORDER BY s.issue_id, s.created_at, s.id
            """
        )
    ).fetchall()

    seen: dict[str, int] = {}
    crossed: dict[str, object] = {}
    for issue_id, created_at in qualifying:
        seen[issue_id] = seen.get(issue_id, 0) + 1
        if seen[issue_id] == CONFIRMS:
            crossed[issue_id] = created_at
    for issue_id, moment in crossed.items():
        bind.execute(
            sa.text("UPDATE issues SET confirmed_at = :moment WHERE id = :id"),
            {"moment": moment, "id": issue_id},
        )

    # Status followed the old rule, so re-derive it for the two statuses the
    # crowd owns. Anything further along was moved by a person and is left be.
    op.execute(
        "UPDATE issues SET status = 'community_verified'"
        " WHERE status = 'reported' AND confirmed_at IS NOT NULL"
    )
    op.execute(
        "UPDATE issues SET status = 'reported'"
        " WHERE status = 'community_verified' AND confirmed_at IS NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.drop_column('confirmed_at')
        batch_op.drop_column('photo_support_count')
    op.drop_index('ix_fix_date_votes_user_issue', table_name='fix_date_votes')
    op.drop_table('fix_date_votes')
    op.drop_index('ix_fix_dates_created_by', table_name='fix_dates')
    op.drop_table('fix_dates')
