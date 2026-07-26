"""Exercise migration 0036 against a minimal SQLite 0035-style schema."""

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
MIGRATION_PATH = ROOT / "backend/migrations/versions/0036_remove_configurable_about_fields.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0036", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0036 konnte nicht geladen werden.")
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
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0036-") as directory:
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
                    project_website_url VARCHAR(500),
                    repository_url VARCHAR(500),
                    release_url VARCHAR(500),
                    issue_url VARCHAR(500),
                    license_notice VARCHAR(1000),
                    imprint_operator_name VARCHAR(200),
                    imprint_address TEXT,
                    imprint_email VARCHAR(255),
                    imprint_phone VARCHAR(100),
                    imprint_responsible_person VARCHAR(200),
                    imprint_registry_info VARCHAR(500),
                    imprint_vat_id VARCHAR(100),
                    imprint_free_text TEXT,
                    feedback_enabled BOOLEAN NOT NULL DEFAULT 0,
                    feedback_folder VARCHAR(500) NOT NULL DEFAULT 'DocOfHome/Feedback',
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
            assert "feedback_enabled" not in columns(connection)
            assert "imprint_email" not in columns(connection)
            assert "repository_url" not in columns(connection)
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()
            assert {"feedback_enabled", "imprint_email", "repository_url"} <= columns(connection)
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "feedback_folder" not in columns(connection)
    print("Migration 0036: Upgrade, Downgrade und erneutes Upgrade erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
