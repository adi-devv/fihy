"""fix date time

Revision ID: 0009_fix_date_time
Revises: 0008_account_deletion
Create Date: 2026-08-28 00:08:40.586126
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0009_fix_date_time'
down_revision: str | None = '0008_account_deletion'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable on purpose: days proposed before the poll carried an hour keep
    # working, and "no time settled yet" stays a state a person can be in.
    with op.batch_alter_table("fix_dates", schema=None) as batch_op:
        batch_op.add_column(sa.Column("fix_time", sa.Time(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("fix_dates", schema=None) as batch_op:
        batch_op.drop_column("fix_time")
