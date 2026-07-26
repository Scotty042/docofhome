"""Exercise migration 0031 against representative SQLite 0030 tables."""

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
    "0031_cabinet_components_and_rows_placements.py"
)


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0031", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0031 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def checks(connection: sa.Connection) -> dict[str, str]:
    return {
        item["name"]: item["sqltext"]
        for item in sa.inspect(connection).get_check_constraints("electrical_connections")
        if item.get("name")
    }


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0031-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'migration.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE electrical_distributions (id VARCHAR(32) PRIMARY KEY)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE electrical_distribution_areas (id VARCHAR(32) PRIMARY KEY)"
            )
            connection.exec_driver_sql("CREATE TABLE assets (id VARCHAR(32) PRIMARY KEY)")
            connection.exec_driver_sql(
                "CREATE TABLE electrical_asset_placements ("
                "id VARCHAR(32) PRIMARY KEY, distribution_id VARCHAR(32) NOT NULL, "
                "area_id VARCHAR(32) NOT NULL, asset_id VARCHAR(32) NOT NULL, "
                "row_number INTEGER NOT NULL, start_position INTEGER NOT NULL, "
                "module_width INTEGER NOT NULL, created_at DATETIME NOT NULL, "
                "updated_at DATETIME NOT NULL, deleted_at DATETIME)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE electrical_connections ("
                "id VARCHAR(32) PRIMARY KEY, source_kind VARCHAR(30) NOT NULL, "
                "source_id VARCHAR(32) NOT NULL, target_kind VARCHAR(30) NOT NULL, "
                "target_id VARCHAR(32) NOT NULL, connection_type VARCHAR(20) NOT NULL, "
                "deleted_at DATETIME, "
                "CONSTRAINT ck_electrical_connections_source_kind CHECK ("
                "source_kind IN ('grid_connection','asset','distribution',"
                "'protective_device','circuit')), "
                "CONSTRAINT ck_electrical_connections_target_kind CHECK ("
                "target_kind IN ('asset','distribution','protective_device','circuit')))"
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()

        with engine.begin() as connection:
            columns = {
                item["name"]: item
                for item in sa.inspect(connection).get_columns(
                    "electrical_asset_placements"
                )
            }
            assert columns["area_id"]["nullable"] is True
            assert "electrical_cabinet_components" in sa.inspect(connection).get_table_names()
            constraint_sql = checks(connection)
            assert "cabinet_component" in constraint_sql[
                "ck_electrical_connections_source_kind"
            ]
            assert "cabinet_component" in constraint_sql[
                "ck_electrical_connections_target_kind"
            ]
            connection.exec_driver_sql(
                "INSERT INTO electrical_distributions (id) VALUES ('distribution')"
            )
            connection.exec_driver_sql("INSERT INTO assets (id) VALUES ('asset')")
            connection.exec_driver_sql(
                "INSERT INTO electrical_asset_placements "
                "(id, distribution_id, area_id, asset_id, row_number, start_position, "
                "module_width, created_at, updated_at) VALUES "
                "('placement','distribution',NULL,'asset',1,1,1,CURRENT_TIMESTAMP,"
                "CURRENT_TIMESTAMP)"
            )
            connection.exec_driver_sql(
                "INSERT INTO electrical_cabinet_components "
                "(id, distribution_id, area_id, component_type, name, row_number, "
                "start_position, module_width, phase_l1, phase_l2, phase_l3, neutral, "
                "protective_earth, created_at, updated_at) VALUES "
                "('block','distribution',NULL,'phase_distribution_block','L1/L2/L3',"
                "1,2,3,1,1,1,0,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
            )
            connection.exec_driver_sql(
                "INSERT INTO electrical_connections "
                "(id, source_kind, source_id, target_kind, target_id, connection_type) "
                "VALUES ('wire','grid_connection','grid','cabinet_component','block','wire')"
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()

        with engine.begin() as connection:
            assert "electrical_cabinet_components" not in sa.inspect(connection).get_table_names()
            columns = {
                item["name"]: item
                for item in sa.inspect(connection).get_columns(
                    "electrical_asset_placements"
                )
            }
            assert columns["area_id"]["nullable"] is False
            constraint_sql = checks(connection)
            assert "cabinet_component" not in constraint_sql[
                "ck_electrical_connections_source_kind"
            ]
            assert "cabinet_component" not in constraint_sql[
                "ck_electrical_connections_target_kind"
            ]

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "electrical_cabinet_components" in sa.inspect(connection).get_table_names()

    print("Migration 0031: Upgrade, Downgrade und erneutes Upgrade erfolgreich geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
