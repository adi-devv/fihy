"""letters go out by email, and the replies come back

The reply address is the correlation key: unguessable, unique, and carried in
the envelope, so it survives a mail client mangling the subject or dropping the
threading headers.

Revision ID: 0007_email_replies
Revises: 0006_escalations
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0007_email_replies'
down_revision: str | None = '0006_escalations'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ADDED = [
    ('recipient', sa.String(length=320)),
    ('reply_token', sa.String(length=40)),
    ('message_id', sa.String(length=300)),
    ('delivered_at', sa.DateTime(timezone=True)),
    ('bounced_at', sa.DateTime(timezone=True)),
]


def upgrade() -> None:
    op.create_table(
        'escalation_messages',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('escalation_id', sa.String(length=32), nullable=False),
        sa.Column(
            'direction',
            sa.Enum('outbound', 'inbound', name='messagedirection', native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column('sender', sa.String(length=320), nullable=False),
        sa.Column('subject', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('message_id', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['escalation_id'], ['escalations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_escalation_messages_thread', 'escalation_messages', ['escalation_id', 'created_at']
    )

    # Every one is nullable, so no rebuild and no backfill. A unique *index*
    # rather than a unique constraint for the same reason: adding a constraint
    # to an existing table means recreating it on SQLite.
    for name, kind in ADDED:
        op.add_column('escalations', sa.Column(name, kind, nullable=True))
    op.create_index(
        'uq_escalations_reply_token', 'escalations', ['reply_token'], unique=True
    )


def downgrade() -> None:
    op.drop_index('uq_escalations_reply_token', table_name='escalations')
    for name, _ in reversed(ADDED):
        op.drop_column('escalations', name)
    op.drop_index('ix_escalation_messages_thread', table_name='escalation_messages')
    op.drop_table('escalation_messages')
