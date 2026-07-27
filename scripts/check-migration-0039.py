"""Exercise migration 0039 against a minimal SQLite 0038-style schema."""

from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "backend/migrations/versions/0039_release_1_6_2_integrity.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0039", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0039 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def columns(connection: sa.Connection, table: str) -> set[str]:
    return {str(item["name"]) for item in sa.inspect(connection).get_columns(table)}


def indexes(connection: sa.Connection, table: str) -> dict[str, dict[str, object]]:
    return {
        str(item["name"]): item
        for item in sa.inspect(connection).get_indexes(table)
        if item.get("name")
    }


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0039-") as directory:
        path = Path(directory) / "migration.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE work_items (
                    id CHAR(32) PRIMARY KEY,
                    item_type VARCHAR(20) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    due_at DATETIME,
                    deleted_at DATETIME
                );
                CREATE TABLE electrical_cabinet_components (
                    id CHAR(32) PRIMARY KEY,
                    component_type VARCHAR(40) NOT NULL,
                    name VARCHAR(150) NOT NULL
                );
                INSERT INTO electrical_cabinet_components VALUES
                    ('22222222222222222222222222222222', 'phase_rail', 'L1-Schiene');
                CREATE TABLE electrical_distributions (
                    id CHAR(32) PRIMARY KEY,
                    layout_mode VARCHAR(20) NOT NULL,
                    CONSTRAINT ck_electrical_distributions_layout_mode
                        CHECK (layout_mode IN ('rows', 'sections'))
                );
                INSERT INTO electrical_distributions VALUES
                    ('11111111111111111111111111111111', 'rows');
                """
            )
            connection.commit()

        engine = sa.create_engine(f"sqlite:///{path}")
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "automation_key" in columns(connection, "work_items")
            assert "mounting_side" in columns(
                connection, "electrical_cabinet_components"
            )
            mounting_side = connection.scalar(
                sa.text(
                    "SELECT mounting_side FROM electrical_cabinet_components LIMIT 1"
                )
            )
            assert mounting_side == "below"
            assert indexes(connection, "work_items")["uq_work_items_automation_key"][
                "unique"
            ]
            connection.execute(
                sa.text(
                    "INSERT INTO work_items "
                    "(id, item_type, title, status, automation_key) "
                    "VALUES ('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'task', 'A', 'open', 'meter:1')"
                )
            )
            try:
                connection.execute(
                    sa.text(
                        "INSERT INTO work_items "
                        "(id, item_type, title, status, automation_key) "
                        "VALUES ('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'task', "
                        "'B', 'open', 'meter:1')"
                    )
                )
            except sa.exc.IntegrityError:
                pass
            else:
                raise AssertionError("automation_key muss eindeutig sein")
            connection.execute(
                sa.text(
                    "UPDATE electrical_distributions SET layout_mode='junction_box'"
                )
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()
            assert "automation_key" not in columns(connection, "work_items")
            assert "mounting_side" not in columns(
                connection, "electrical_cabinet_components"
            )
            mode = connection.scalar(
                sa.text("SELECT layout_mode FROM electrical_distributions LIMIT 1")
            )
            assert mode == "rows"

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "automation_key" in columns(connection, "work_items")

    print("Migration 0039: Upgrade, Eindeutigkeit, Downgrade und Re-Upgrade erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
