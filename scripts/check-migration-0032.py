"""Exercise migration 0032 against representative SQLite 0031 tables."""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "backend" / "migrations" / "versions" / (
    "0032_asset_and_type_din_width.py"
)


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0032", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0032 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def columns(connection: sa.Connection, table: str) -> dict[str, dict[str, object]]:
    return {
        item["name"]: item
        for item in sa.inspect(connection).get_columns(table)
    }


def constraints(connection: sa.Connection, table: str) -> set[str]:
    return {
        str(item["name"])
        for item in sa.inspect(connection).get_check_constraints(table)
        if item.get("name")
    }


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0032-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'migration.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE asset_types ("
                "id VARCHAR(32) PRIMARY KEY, name VARCHAR(100) NOT NULL, "
                "code_prefix VARCHAR(20) NOT NULL)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE assets ("
                "id VARCHAR(32) PRIMARY KEY, name VARCHAR(150) NOT NULL, "
                "asset_type_id VARCHAR(32) NOT NULL)"
            )
            connection.exec_driver_sql(
                "INSERT INTO asset_types (id, name, code_prefix) "
                "VALUES ('type', 'Smart Meter', 'SM')"
            )
            connection.exec_driver_sql(
                "INSERT INTO assets (id, name, asset_type_id) "
                "VALUES ('asset', 'Hausmessung', 'type')"
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()

        with engine.begin() as connection:
            assert columns(connection, "asset_types")["module_width"]["nullable"] is True
            assert columns(connection, "assets")["module_width"]["nullable"] is True
            assert "ck_asset_types_module_width" in constraints(connection, "asset_types")
            assert "ck_assets_module_width" in constraints(connection, "assets")
            connection.exec_driver_sql(
                "UPDATE asset_types SET module_width = 4 WHERE id = 'type'"
            )
            connection.exec_driver_sql(
                "UPDATE assets SET module_width = 2 WHERE id = 'asset'"
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()

        with engine.begin() as connection:
            assert "module_width" not in columns(connection, "asset_types")
            assert "module_width" not in columns(connection, "assets")
            assert connection.exec_driver_sql(
                "SELECT name FROM assets WHERE id = 'asset'"
            ).scalar_one() == "Hausmessung"

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "module_width" in columns(connection, "asset_types")
            assert "module_width" in columns(connection, "assets")

    print("Migration 0032: Upgrade, Downgrade und erneutes Upgrade erfolgreich geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
