from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path
from types import ModuleType

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend/migrations/versions/0035_about_page_and_feedback.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0035", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def columns(connection: sa.Connection) -> set[str]:
    table_columns = sa.inspect(connection).get_columns("application_settings")
    return {str(item["name"]) for item in table_columns}


def test_about_settings_migration_upgrade_downgrade(tmp_path: Path) -> None:
    path = tmp_path / "about.sqlite3"
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
    migration = load_migration()
    with engine.begin() as connection:
        migration.op = operations(connection)
        migration.upgrade()
        expected = {
            "feedback_enabled",
            "feedback_folder",
            "imprint_email",
            "repository_url",
        }
        assert expected <= columns(connection)
    with engine.begin() as connection:
        migration.op = operations(connection)
        migration.downgrade()
        assert "feedback_enabled" not in columns(connection)
    with engine.begin() as connection:
        migration.op = operations(connection)
        migration.upgrade()
        assert "feedback_folder" in columns(connection)
