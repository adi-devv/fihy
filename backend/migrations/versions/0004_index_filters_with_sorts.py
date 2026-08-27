"""index the filters alongside their sorts

Every one of these replaces a single-column index with a composite that leads
with the same column, so nothing loses a lookup path: what they gain is the
sort. Paging a person's own reports, a person's own supports, and an issue's
gallery all filtered on one column and then ordered by created_at, which meant
the planner read the whole match and sorted it in a temp b-tree.

Revision ID: 0004_index_filters
Revises: 0003_supports
"""
from collections.abc import Sequence

from alembic import op

revision: str = '0004_index_filters'
down_revision: str | None = '0003_supports'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Plain index operations rather than batch_alter_table: an index needs no table
# rebuild on either backend, and batch mode risks one for nothing.
REPLACEMENTS = [
    # table, old single-column index, new composite, columns
    ('issues', 'ix_issues_reporter_id', 'ix_issues_reporter_created', ['reporter_id', 'created_at']),
    ('supports', 'ix_supports_user_id', 'ix_supports_user_created', ['user_id', 'created_at']),
    ('issue_photos', 'ix_issue_photos_issue_id', 'ix_issue_photos_issue_created', ['issue_id', 'created_at']),
    ('otp_request_log', 'ix_otp_request_log_ip', 'ix_otp_request_log_ip_created', ['ip', 'created_at']),
]

# Already covered by a composite that leads with the same column.
REDUNDANT = [
    ('supports', 'ix_supports_issue_id', ['issue_id']),
    ('activity_events', 'ix_activity_events_user_id', ['user_id']),
]


def upgrade() -> None:
    for table, old, new, columns in REPLACEMENTS:
        op.create_index(new, table, columns)
        op.drop_index(old, table_name=table)
    for table, name, _ in REDUNDANT:
        op.drop_index(name, table_name=table)


def downgrade() -> None:
    for table, name, columns in REDUNDANT:
        op.create_index(name, table, columns)
    for table, old, new, columns in REPLACEMENTS:
        op.create_index(old, table, [columns[0]])
        op.drop_index(new, table_name=table)
