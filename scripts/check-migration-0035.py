"""Exercise migration 0035 against a minimal SQLite 0034-style schema."""

from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
from pathlib import Path
from types import ModuleType

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "backend/migrations/versions/0035_about_page_and_feedback.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0035", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0035 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def columns(connection: sa.Connection) -> set[str]:
    return {
        str(item["name"])
        for item in sa.inspect(connection).get_columns("application_settings")
    }


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0035-") as directory:
        path = Path(directory) / "migration.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                CREATE TABLE application_settings (
                    id INTEGER PRIMARY KEY,
                    installation_name VARCHAR(100) NOT NULL,
                    language VARCHAR(10) NOT NULL,
                    timezone VARCHAR(100) NOT NULL,
                    theme VARCHAR(20) NOT NULL,
                    enabled_modules_json VARCHAR NOT NULL,
                    online_product_image_search_enabled BOOLEAN NOT NULL,
                    setup_completed_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                """
            )
        engine = sa.create_engine(f"sqlite:///{path}")
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert {
                "repository_url",
                "imprint_email",
                "feedback_enabled",
                "feedback_folder",
            } <= columns(connection)
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()
            assert "feedback_enabled" not in columns(connection)
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "feedback_folder" in columns(connection)
    print("Migration 0035: Upgrade, Downgrade und erneutes Upgrade erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
