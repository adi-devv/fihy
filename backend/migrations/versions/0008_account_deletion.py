"""account deletion: the row survives, the person does not

Revision ID: 0008_account_deletion
Revises: 0007_email_replies
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0008_account_deletion'
down_revision: str | None = '0007_email_replies'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable, so no rebuild and no backfill: every existing account is live.
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))



def downgrade() -> None:
    op.drop_column('users', 'deleted_at')

