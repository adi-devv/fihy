"""Migrations are the schema of record, so they have to agree with the models.

`create_all` is what the test suite uses for speed; if these two ever drift,
every other test keeps passing while a deploy breaks. This is the test that
notices.
"""
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app import migrations
from app.models import Base


def migrated(tmp_path, revision: str = "head"):
    engine = create_engine(f"sqlite:///{tmp_path / 'parity.db'}")
    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.upgrade(config, revision)
    return engine


def test_upgrading_from_empty_matches_the_models(tmp_path):
    engine = migrated(tmp_path)
    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection, opts={"compare_type": True}
        )
        assert compare_metadata(context, Base.metadata) == []


def test_every_model_table_is_created(tmp_path):
    engine = migrated(tmp_path)
    tables = set(inspect(engine).get_table_names())
    assert set(Base.metadata.tables) <= tables


def test_comment_count_backfills_onto_existing_rows(tmp_path):
    """The column arrived after issues already existed. Autogenerate emitted a
    bare NOT NULL, which cannot be applied to a populated table; 0002 carries a
    server default for exactly this."""
    engine = migrated(tmp_path, "0001_initial")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO users (id, phone, display_name, created_at)"
            " VALUES ('u1', '+919000000001', 'Existing', datetime('now'))"
        )
        connection.exec_driver_sql(
            "INSERT INTO issues (id, reporter_id, client_report_id, title,"
            " description, category, severity, status, latitude, longitude,"
            " confirmation_count, created_at, updated_at)"
            " VALUES ('i1', 'u1', 'r1', 'Older report', '', 'garbage', 'low',"
            " 'reported', 19.0, 72.8, 0, datetime('now'), datetime('now'))"
        )

    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT comment_count FROM issues WHERE id = 'i1'"
        ).one()
        assert row[0] == 0


def test_downgrade_returns_to_the_previous_revision(tmp_path):
    engine = migrated(tmp_path)
    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.downgrade(config, "0001_initial")
    tables = set(inspect(engine).get_table_names())
    assert "comments" not in tables
    assert "issues" in tables


def seed_at_0002(engine) -> None:
    """A database as it looked before supports existed: two people who
    confirmed, commented, or both, and photos with nobody credited."""
    with engine.begin() as connection:
        run = connection.exec_driver_sql
        for uid, phone, name in (
            ("u1", "+919000000001", "Reporter"),
            ("u2", "+919000000002", "Confirmer"),
            ("u3", "+919000000003", "Commenter"),
            ("u4", "+919000000004", "Both"),
        ):
            run(
                "INSERT INTO users (id, phone, display_name, created_at)"
                f" VALUES ('{uid}', '{phone}', '{name}', datetime('now'))"
            )
        run(
            "INSERT INTO issues (id, reporter_id, client_report_id, title,"
            " description, category, severity, status, latitude, longitude,"
            " confirmation_count, comment_count, created_at, updated_at)"
            " VALUES ('i1', 'u1', 'r1', 'Older report', '', 'garbage', 'low',"
            " 'reported', 19.0, 72.8, 99, 99, datetime('now'), datetime('now'))"
        )
        run(
            "INSERT INTO issue_photos (id, issue_id, position, original_key,"
            " thumbnail_key, created_at)"
            " VALUES ('p1', 'i1', 0, 'a/o.jpg', 'a/t.jpg', datetime('now'))"
        )
        run(
            "INSERT INTO confirmations (id, issue_id, user_id, note, created_at)"
            " VALUES ('c1', 'i1', 'u2', NULL, datetime('now'))"
        )
        run(
            "INSERT INTO confirmations (id, issue_id, user_id, note, created_at)"
            " VALUES ('c2', 'i1', 'u4', 'a note that was never shown', datetime('now'))"
        )
        for cid, author, body, when in (
            ("m1", "u3", "First thing I said", "2026-01-01 10:00:00"),
            ("m2", "u3", "Second thing I said", "2026-01-01 11:00:00"),
            ("m3", "u4", "I also wrote this", "2026-01-01 12:00:00"),
        ):
            run(
                "INSERT INTO comments (id, issue_id, author_id, body, created_at)"
                f" VALUES ('{cid}', 'i1', '{author}', '{body}', '{when}')"
            )
        run(
            "INSERT INTO activity_events (id, user_id, issue_id, actor_id, type, created_at)"
            " VALUES ('e1', 'u1', 'i1', 'u2', 'confirmation_received', datetime('now'))"
        )
        run(
            "INSERT INTO activity_events (id, user_id, issue_id, actor_id, type, created_at)"
            " VALUES ('e2', 'u1', 'i1', 'u3', 'comment_received', datetime('now'))"
        )


def test_supports_merge_keeps_one_row_per_person(tmp_path):
    engine = migrated(tmp_path, "0002_comments")
    seed_at_0002(engine)
    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    with engine.connect() as connection:
        rows = connection.exec_driver_sql(
            "SELECT user_id, body FROM supports ORDER BY user_id"
        ).fetchall()

    by_user = dict(rows)
    assert set(by_user) == {"u2", "u3", "u4"}, "one support per person, no duplicates"
    assert by_user["u2"] is None, "a bare confirmation stays a bare support"
    assert by_user["u3"] == "First thing I said\n\nSecond thing I said", (
        "several comments from one person fold into one body, oldest first"
    )
    # Confirmed and commented: the comment is the text, and nothing is dropped.
    assert by_user["u4"] == "I also wrote this"


def test_supports_merge_backfills_photos_and_counts(tmp_path):
    engine = migrated(tmp_path, "0002_comments")
    seed_at_0002(engine)
    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    with engine.connect() as connection:
        contributor = connection.exec_driver_sql(
            "SELECT contributor_id, support_id FROM issue_photos WHERE id = 'p1'"
        ).one()
        assert contributor == ("u1", None), "an unattributed photo credits the reporter"

        counts = connection.exec_driver_sql(
            "SELECT confirmation_count, comment_count, photo_count FROM issues"
            " WHERE id = 'i1'"
        ).one()
        # Seeded as 99/99 on purpose: the tallies are recomputed, not trusted.
        assert counts == (3, 2, 1)

        kinds = connection.exec_driver_sql(
            "SELECT DISTINCT type FROM activity_events"
        ).fetchall()
        assert kinds == [("support_received",)]


def test_supports_downgrade_restores_the_old_shape(tmp_path):
    engine = migrated(tmp_path, "0002_comments")
    seed_at_0002(engine)
    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with engine.begin() as connection:
        config = migrations.config()
        config.attributes["connection"] = connection
        command.downgrade(config, "0002_comments")

    tables = set(inspect(engine).get_table_names())
    assert {"confirmations", "comments"} <= tables
    assert "supports" not in tables
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT COUNT(*) FROM confirmations"
        ).scalar() == 3


# Each of these is a filter and the sort that always follows it. Split across
# two indexes the planner reads every match and sorts it in a temp b-tree, which
# no test would notice and every paged screen would pay for.
PAGING_INDEXES = {
    "issues": ("ix_issues_reporter_created", ["reporter_id", "created_at"]),
    "supports": ("ix_supports_user_created", ["user_id", "created_at"]),
    "issue_photos": ("ix_issue_photos_issue_created", ["issue_id", "created_at"]),
    "otp_request_log": ("ix_otp_request_log_ip_created", ["ip", "created_at"]),
    "activity_events": ("ix_activity_user_created", ["user_id", "created_at"]),
}


def test_paged_reads_have_a_composite_index(tmp_path):
    engine = migrated(tmp_path)
    inspector = inspect(engine)
    for table, (name, columns) in PAGING_INDEXES.items():
        found = {i["name"]: i["column_names"] for i in inspector.get_indexes(table)}
        assert name in found, f"{table} lost {name}"
        assert found[name] == columns, f"{name} columns changed"


def test_the_distance_prefilter_is_indexed(tmp_path):
    """Nearby cannot sort by an index - the order is computed - so the bounding
    box is the only thing keeping it off a full scan."""
    engine = migrated(tmp_path)
    found = {i["name"]: i["column_names"] for i in inspect(engine).get_indexes("issues")}
    assert found.get("ix_issues_lat_lng") == ["latitude", "longitude"]


def test_no_index_is_a_prefix_of_another(tmp_path):
    """A single-column index whose column already leads a composite earns
    nothing and is paid for on every write."""
    engine = migrated(tmp_path)
    inspector = inspect(engine)
    for table in inspect(engine).get_table_names():
        if table == "alembic_version":
            continue
        indexes = [
            (i["name"], list(i["column_names"]))
            for i in inspector.get_indexes(table)
        ]
        # A UNIQUE(a, b) constraint is an index on (a, b), so a declared index
        # with the same columns is paid for twice and used once.
        constraints = [
            (f"unique{tuple(c['column_names'])}", list(c["column_names"]))
            for c in inspector.get_unique_constraints(table)
        ]
        plain = [
            (i["name"], list(i["column_names"]))
            for i in inspector.get_indexes(table)
            if not i.get("unique")
        ]
        for name, columns in plain:
            covered = [
                other
                for other, other_columns in indexes + constraints
                if other != name
                and len(other_columns) >= len(columns)
                and other_columns[: len(columns)] == columns
            ]
            assert not covered, f"{table}.{name} is already covered by {covered}"
