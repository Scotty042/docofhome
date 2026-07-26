"""Verify migration 0033 removes the legacy single-target topology index."""

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
    "0033_remove_legacy_single_target_topology_index.py"
)
LEGACY_INDEX = "uq_electrical_connections_active_target"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0033", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0033 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def index_names(connection: sa.Connection) -> set[str]:
    return {
        str(item["name"])
        for item in sa.inspect(connection).get_indexes("electrical_connections")
        if item.get("name")
    }


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0033-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'migration.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE electrical_connections ("
                "id VARCHAR(32) PRIMARY KEY, source_kind VARCHAR(30) NOT NULL, "
                "source_id VARCHAR(32) NOT NULL, target_kind VARCHAR(30) NOT NULL, "
                "target_id VARCHAR(32) NOT NULL, deleted_at DATETIME NULL)"
            )
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX uq_electrical_connections_active_pair ON "
                "electrical_connections (source_kind, source_id, target_kind, target_id) "
                "WHERE deleted_at IS NULL"
            )
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX uq_electrical_connections_active_target ON "
                "electrical_connections (target_kind, target_id) "
                "WHERE deleted_at IS NULL"
            )
            assert LEGACY_INDEX in index_names(connection)

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()

        with engine.begin() as connection:
            assert LEGACY_INDEX not in index_names(connection)
            connection.exec_driver_sql(
                "INSERT INTO electrical_connections "
                "(id, source_kind, source_id, target_kind, target_id, deleted_at) "
                "VALUES ('one', 'asset', 'grid-meter', 'cabinet_component', "
                "'phase-block', NULL)"
            )
            connection.exec_driver_sql(
                "INSERT INTO electrical_connections "
                "(id, source_kind, source_id, target_kind, target_id, deleted_at) "
                "VALUES ('two', 'asset', 'pv-inverter', 'cabinet_component', "
                "'phase-block', NULL)"
            )
            assert connection.exec_driver_sql(
                "SELECT COUNT(*) FROM electrical_connections "
                "WHERE target_id = 'phase-block'"
            ).scalar_one() == 2

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()
            assert LEGACY_INDEX not in index_names(connection)

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert LEGACY_INDEX not in index_names(connection)

    print("Migration 0033: Legacy-Zielindex entfernt; zwei Einspeisungen möglich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
