"""comments

Revision ID: 0002_comments
Revises: 0001_initial
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0002_comments'
down_revision: str | None = '0001_initial'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'comments',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('issue_id', sa.String(length=32), nullable=False),
        sa.Column('author_id', sa.String(length=32), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_comments_author_id'), ['author_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_comments_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_comments_issue_created', ['issue_id', 'created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_comments_issue_id'), ['issue_id'], unique=False)

    # Autogenerate emits this as a bare NOT NULL, which cannot be applied to a
    # table that already has rows. The server default backfills them, and is
    # then dropped so the column matches the model, which defaults in Python.
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('comment_count', sa.Integer(), nullable=False, server_default=sa.text('0'))
        )
    # A separate batch: SQLite applies the add in place, but dropping the
    # default rebuilds the table, and the two cannot share one context.
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.alter_column('comment_count', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.drop_column('comment_count')

    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_comments_issue_id'))
        batch_op.drop_index('ix_comments_issue_created')
        batch_op.drop_index(batch_op.f('ix_comments_created_at'))
        batch_op.drop_index(batch_op.f('ix_comments_author_id'))

    op.drop_table('comments')
