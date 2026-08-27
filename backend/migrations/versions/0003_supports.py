"""supports: confirmations and comments become one row, photos gain a contributor

Revision ID: 0003_supports
Revises: 0002_comments
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0003_supports'
down_revision: str | None = '0002_comments'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'supports',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('issue_id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_id', 'user_id', name='uq_supports_issue_user'),
    )
    with op.batch_alter_table('supports', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_supports_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_supports_issue_created', ['issue_id', 'created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_supports_issue_id'), ['issue_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supports_user_id'), ['user_id'], unique=False)

    # A confirmation was already one row per person per issue, so it becomes a
    # support directly; its unused `note` is the body it never got to carry.
    op.execute(
        """
        INSERT INTO supports (id, issue_id, user_id, body, created_at, updated_at)
        SELECT id, issue_id, user_id, note, created_at, created_at
        FROM confirmations
        """
    )

    # Comments were many per person; a support is one. Merge them in Python
    # rather than SQL: the concatenation needs GROUP_CONCAT on SQLite and
    # string_agg on PostgreSQL, and this runs once.
    bind = op.get_bind()
    comments = bind.execute(
        sa.text(
            "SELECT issue_id, author_id, body FROM comments"
            " ORDER BY issue_id, author_id, created_at, id"
        )
    ).fetchall()

    merged: dict[tuple[str, str], list[str]] = {}
    for issue_id, author_id, body in comments:
        merged.setdefault((issue_id, author_id), []).append(body)

    existing = {
        (issue_id, user_id)
        for issue_id, user_id in bind.execute(
            sa.text("SELECT issue_id, user_id FROM supports")
        ).fetchall()
    }

    for (issue_id, author_id), bodies in merged.items():
        text = "\n\n".join(bodies)
        if (issue_id, author_id) in existing:
            # They confirmed and commented: the support is already there, and
            # what it is missing is the words.
            bind.execute(
                sa.text(
                    "UPDATE supports SET body = :body"
                    " WHERE issue_id = :issue_id AND user_id = :user_id"
                ),
                {"body": text, "issue_id": issue_id, "user_id": author_id},
            )
            continue
        first = bind.execute(
            sa.text(
                "SELECT id, created_at FROM comments"
                " WHERE issue_id = :issue_id AND author_id = :author_id"
                " ORDER BY created_at, id LIMIT 1"
            ),
            {"issue_id": issue_id, "author_id": author_id},
        ).one()
        bind.execute(
            sa.text(
                "INSERT INTO supports (id, issue_id, user_id, body, created_at, updated_at)"
                " VALUES (:id, :issue_id, :user_id, :body, :created_at, :created_at)"
            ),
            {
                "id": first[0],
                "issue_id": issue_id,
                "user_id": author_id,
                "body": text,
                "created_at": first[1],
            },
        )

    # Photos: added nullable so existing rows survive, backfilled to whoever
    # reported the issue, then pinned NOT NULL. A bare NOT NULL add would fail
    # on any table that already has rows.
    with op.batch_alter_table('issue_photos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contributor_id', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('support_id', sa.String(length=32), nullable=True))

    op.execute(
        """
        UPDATE issue_photos
           SET contributor_id = (
                 SELECT reporter_id FROM issues WHERE issues.id = issue_photos.issue_id
               )
         WHERE contributor_id IS NULL
        """
    )
    # An issue_photos row whose issue vanished has nobody to credit and nothing
    # to point at; it cannot be made NOT NULL, and it is already unreachable.
    op.execute("DELETE FROM issue_photos WHERE contributor_id IS NULL")

    with op.batch_alter_table('issue_photos', schema=None) as batch_op:
        batch_op.alter_column(
            'contributor_id', existing_type=sa.String(length=32), nullable=False
        )
        batch_op.create_index(batch_op.f('ix_issue_photos_contributor_id'), ['contributor_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_issue_photos_support_id'), ['support_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_issue_photos_created_at'), ['created_at'], unique=False)
        batch_op.create_foreign_key(
            'fk_issue_photos_contributor', 'users', ['contributor_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_issue_photos_support', 'supports', ['support_id'], ['id'], ondelete='CASCADE'
        )

    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('photo_count', sa.Integer(), nullable=False, server_default=sa.text('0'))
        )
        batch_op.add_column(sa.Column('ai_summary', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ai_summary_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column('ai_summary_voices', sa.Integer(), nullable=False, server_default=sa.text('0'))
        )
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.alter_column('photo_count', server_default=None)
        batch_op.alter_column('ai_summary_voices', server_default=None)

    # Every tally is derived, so recompute rather than trusting what was there.
    op.execute(
        """
        UPDATE issues SET
            confirmation_count = (SELECT COUNT(*) FROM supports WHERE supports.issue_id = issues.id),
            comment_count = (SELECT COUNT(*) FROM supports
                              WHERE supports.issue_id = issues.id
                                AND supports.body IS NOT NULL AND supports.body <> ''),
            photo_count = (SELECT COUNT(*) FROM issue_photos WHERE issue_photos.issue_id = issues.id)
        """
    )

    # Both old event kinds described the same act.
    op.execute(
        "UPDATE activity_events SET type = 'support_received'"
        " WHERE type IN ('confirmation_received', 'comment_received')"
    )

    op.drop_table('comments')
    op.drop_table('confirmations')


def downgrade() -> None:
    op.create_table(
        'confirmations',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('issue_id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_id', 'user_id', name='uq_confirmations_issue_user'),
    )
    with op.batch_alter_table('confirmations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_confirmations_issue_id'), ['issue_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_confirmations_user_id'), ['user_id'], unique=False)

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

    op.execute(
        """
        INSERT INTO confirmations (id, issue_id, user_id, note, created_at)
        SELECT id, issue_id, user_id, body, created_at FROM supports
        """
    )
    op.execute(
        """
        INSERT INTO comments (id, issue_id, author_id, body, created_at)
        SELECT id, issue_id, user_id, body, created_at
        FROM supports WHERE body IS NOT NULL AND body <> ''
        """
    )

    # Photos that arrived with a support have no home in the old shape.
    op.execute("DELETE FROM issue_photos WHERE support_id IS NOT NULL")

    with op.batch_alter_table('issue_photos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_issue_photos_support', type_='foreignkey')
        batch_op.drop_constraint('fk_issue_photos_contributor', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_issue_photos_created_at'))
        batch_op.drop_index(batch_op.f('ix_issue_photos_support_id'))
        batch_op.drop_index(batch_op.f('ix_issue_photos_contributor_id'))
        batch_op.drop_column('support_id')
        batch_op.drop_column('contributor_id')

    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.drop_column('ai_summary_voices')
        batch_op.drop_column('ai_summary_at')
        batch_op.drop_column('ai_summary')
        batch_op.drop_column('photo_count')

    op.execute(
        "UPDATE activity_events SET type = 'confirmation_received'"
        " WHERE type = 'support_received'"
    )

    with op.batch_alter_table('supports', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_supports_user_id'))
        batch_op.drop_index(batch_op.f('ix_supports_issue_id'))
        batch_op.drop_index('ix_supports_issue_created')
        batch_op.drop_index(batch_op.f('ix_supports_created_at'))
    op.drop_table('supports')
