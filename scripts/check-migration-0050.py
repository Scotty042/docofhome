"""Verify migration 0050 against a representative SQLite 0049 work schema."""
from importlib import util
from pathlib import Path
import tempfile

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend/migrations/versions/0050_work_history_and_subjects.py"


def load():
    spec = util.spec_from_file_location("migration_0050", MIGRATION)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0050-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'test.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("""
                CREATE TABLE work_items (
                    id CHAR(32) PRIMARY KEY,
                    item_type VARCHAR(20) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    target_type VARCHAR(30),
                    target_id CHAR(32),
                    due_at DATETIME,
                    recurrence_days INTEGER,
                    recurrence_mode VARCHAR(20) NOT NULL DEFAULT 'none',
                    calendar_months INTEGER,
                    calendar_day INTEGER,
                    calendar_month INTEGER,
                    calendar_last_day BOOLEAN NOT NULL DEFAULT 0,
                    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
                    automation_key VARCHAR(255),
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    completed_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE work_item_events (
                    id CHAR(32) PRIMARY KEY,
                    work_item_id CHAR(32) NOT NULL,
                    event_type VARCHAR(20) NOT NULL,
                    note TEXT,
                    due_at_before DATETIME,
                    due_at_after DATETIME,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY(work_item_id) REFERENCES work_items(id)
                )
            """)
            connection.exec_driver_sql("""
                INSERT INTO work_items (
                    id, item_type, title, recurrence_mode, priority,
                    status, created_at, updated_at
                ) VALUES (
                    'item', 'maintenance', 'Filter', 'none', 'normal',
                    'open', '2026-01-01 10:00:00', '2026-01-01 10:00:00'
                )
            """)
            connection.exec_driver_sql("""
                INSERT INTO work_item_events (id, work_item_id, event_type, created_at)
                VALUES ('event', 'item', 'completed', '2025-12-31 12:34:56')
            """)

            migration = load()
            migration.op = operations(connection)
            migration.upgrade()

            inspector = sa.inspect(connection)
            assert {"work_subjects", "work_item_event_attachments"}.issubset(
                set(inspector.get_table_names())
            )
            event_columns = {item["name"]: item for item in inspector.get_columns("work_item_events")}
            assert event_columns["occurred_at"]["nullable"] is False
            occurred_at = connection.execute(
                sa.text("SELECT occurred_at FROM work_item_events WHERE id='event'")
            ).scalar_one()
            assert str(occurred_at).startswith("2025-12-31 12:34:56")
            assert "subject_id" in {
                item["name"] for item in inspector.get_columns("work_items")
            }
            assert "content" in {
                item["name"] for item in inspector.get_columns("work_item_event_attachments")
            }

            connection.execute(sa.text("""
                INSERT INTO work_subjects (
                    id, name, subject_type, created_at, updated_at, deleted_at
                ) VALUES ('subject', 'Penny', 'animal', '2026-08-24', '2026-08-24', NULL)
            """))
            connection.execute(sa.text("UPDATE work_items SET subject_id='subject' WHERE id='item'"))
            connection.execute(
                sa.text("""
                    INSERT INTO work_item_event_attachments (
                        id, event_id, file_name, content_type, size_bytes, content, created_at
                    ) VALUES (
                        'attachment', 'event', 'beleg.txt', 'text/plain', 3, :content, '2026-08-24'
                    )
                """),
                {"content": b"abc"},
            )
            assert connection.execute(
                sa.text("SELECT content FROM work_item_event_attachments WHERE id='attachment'")
            ).scalar_one() == b"abc"

            connection.execute(sa.text("DELETE FROM work_item_event_attachments"))
            connection.execute(sa.text("UPDATE work_items SET subject_id=NULL"))
            connection.execute(sa.text("DELETE FROM work_subjects"))
            migration.downgrade()

            inspector = sa.inspect(connection)
            assert "work_subjects" not in inspector.get_table_names()
            assert "work_item_event_attachments" not in inspector.get_table_names()
            assert "subject_id" not in {
                item["name"] for item in inspector.get_columns("work_items")
            }
            assert "occurred_at" not in {
                item["name"] for item in inspector.get_columns("work_item_events")
            }

    print("Migration 0050: SQLite Upgrade/Backfill/BLOB/Downgrade erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
