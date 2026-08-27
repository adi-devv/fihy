"""escalations: reports raised with the body responsible for them

Revision ID: 0006_escalations
Revises: 0005_fix_dates
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0006_escalations'
down_revision: str | None = '0005_fix_dates'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('escalations',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('issue_id', sa.String(length=32), nullable=False),
    sa.Column('authority', sa.String(length=160), nullable=False),
    sa.Column('subject', sa.String(length=300), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('state', sa.Enum('drafted', 'sent', 'failed', name='escalationstate', native_enum=False, length=32), nullable=False),
    sa.Column('reference', sa.String(length=200), nullable=True),
    sa.Column('detail', sa.Text(), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('checked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('issue_id', name='uq_escalations_issue')
    )
    op.create_index('ix_escalations_state_checked', 'escalations', ['state', 'checked_at'])
    op.create_index('ix_issues_status_confirmed', 'issues', ['status', 'confirmed_at'])


def downgrade() -> None:
    op.drop_index('ix_issues_status_confirmed', table_name='issues')
    op.drop_index('ix_escalations_state_checked', table_name='escalations')
    op.drop_table('escalations')
