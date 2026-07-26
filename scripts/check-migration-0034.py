"""Exercise migration 0034 against a minimal SQLite 0033-style schema."""

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
MIGRATION_PATH = ROOT / "backend" / "migrations" / "versions" / "0034_home_electrical_groups.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0034", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0034 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def columns(connection: sa.Connection, table: str) -> set[str]:
    return {str(item["name"]) for item in sa.inspect(connection).get_columns(table)}


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0034-") as directory:
        path = Path(directory) / "migration.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys=ON;
                CREATE TABLE electrical_components (id CHAR(32) PRIMARY KEY);
                CREATE TABLE electrical_distributions (id CHAR(32) PRIMARY KEY);
                CREATE TABLE electrical_distribution_areas (id CHAR(32) PRIMARY KEY);
                CREATE TABLE electrical_cabinet_components (
                    id CHAR(32) PRIMARY KEY, distribution_id CHAR(32) NOT NULL,
                    area_id CHAR(32), component_type VARCHAR(40) NOT NULL,
                    name VARCHAR(150) NOT NULL, row_number INTEGER NOT NULL,
                    start_position INTEGER NOT NULL, module_width INTEGER NOT NULL,
                    phase_l1 BOOLEAN NOT NULL DEFAULT 0,
                    phase_l2 BOOLEAN NOT NULL DEFAULT 0,
                    phase_l3 BOOLEAN NOT NULL DEFAULT 0,
                    neutral BOOLEAN NOT NULL DEFAULT 0,
                    protective_earth BOOLEAN NOT NULL DEFAULT 0,
                    rated_current_a FLOAT, max_cross_section_mm2 FLOAT,
                    outgoing_connections INTEGER, description TEXT, notes TEXT,
                    created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                );
                CREATE TABLE electrical_protective_devices (
                    id CHAR(32) PRIMARY KEY, distribution_id CHAR(32) NOT NULL,
                    area_id CHAR(32), device_type VARCHAR(20) NOT NULL,
                    row_number INTEGER, start_position INTEGER, module_width INTEGER,
                    rated_current_a FLOAT, residual_current_ma FLOAT,
                    characteristic VARCHAR(30), poles INTEGER,
                    breaking_capacity_ka FLOAT, rcd_type VARCHAR(80),
                    fuse_type VARCHAR(80), spd_type VARCHAR(80),
                    description TEXT, notes TEXT
                );
                """
            )
        engine = sa.create_engine(f"sqlite:///{path}")
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
        with engine.begin() as connection:
            assert {"linked_rcd_device_id", "start_phase"} <= columns(
                connection, "electrical_cabinet_components"
            )
            assert {"assigned_rcd_id", "neutral_rail_id"} <= columns(
                connection, "electrical_protective_devices"
            )
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()
        with engine.begin() as connection:
            assert "linked_rcd_device_id" not in columns(
                connection, "electrical_cabinet_components"
            )
            assert "assigned_rcd_id" not in columns(
                connection, "electrical_protective_devices"
            )
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "start_phase" in columns(connection, "electrical_cabinet_components")
    print("Migration 0034: Upgrade, Downgrade und erneutes Upgrade erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
