"""Exercise migration 0041 against a minimal SQLite 0040-style schema."""

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
MIGRATION_PATH = ROOT / "backend/migrations/versions/0041_repair_phase_rail_connections.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0041", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0041 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0041-") as directory:
        path = Path(directory) / "migration.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                CREATE TABLE electrical_cabinet_components (
                    id TEXT PRIMARY KEY,
                    distribution_id TEXT NOT NULL,
                    area_id TEXT,
                    component_type TEXT NOT NULL,
                    row_number INTEGER NOT NULL,
                    start_position INTEGER NOT NULL,
                    module_width INTEGER NOT NULL,
                    phase_l1 BOOLEAN NOT NULL,
                    phase_l2 BOOLEAN NOT NULL,
                    phase_l3 BOOLEAN NOT NULL,
                    start_phase TEXT,
                    deleted_at DATETIME
                );
                CREATE TABLE electrical_components (
                    id TEXT PRIMARY KEY,
                    deleted_at DATETIME
                );
                CREATE TABLE electrical_protective_devices (
                    id TEXT PRIMARY KEY,
                    distribution_id TEXT NOT NULL,
                    area_id TEXT,
                    row_number INTEGER,
                    start_position INTEGER,
                    poles INTEGER
                );
                CREATE TABLE electrical_connections (
                    id TEXT PRIMARY KEY,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_kind TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    phase_l1 BOOLEAN NOT NULL,
                    phase_l2 BOOLEAN NOT NULL,
                    phase_l3 BOOLEAN NOT NULL,
                    neutral BOOLEAN NOT NULL,
                    protective_earth BOOLEAN NOT NULL,
                    deleted_at DATETIME
                );

                INSERT INTO electrical_cabinet_components VALUES
                    ('rail', 'dist', NULL, 'phase_rail', 1, 1, 6, 1, 1, 1, 'L1', NULL);
                INSERT INTO electrical_components VALUES
                    ('washer', NULL), ('dryer', NULL);
                INSERT INTO electrical_protective_devices VALUES
                    ('washer', 'dist', NULL, 1, 2, 1),
                    ('dryer', 'dist', NULL, 1, 3, 1);
                INSERT INTO electrical_connections VALUES
                    ('c1', 'cabinet_component', 'rail', 'protective_device', 'washer',
                     0, 0, 1, 0, 0, NULL),
                    ('c2', 'cabinet_component', 'rail', 'protective_device', 'dryer',
                     1, 0, 0, 1, 1, NULL);
                """
            )
            connection.commit()

        engine = sa.create_engine(f"sqlite:///{path}")
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            washer = tuple(connection.execute(sa.text(
                "SELECT phase_l1, phase_l2, phase_l3 FROM electrical_connections WHERE id='c1'"
            )).one())
            dryer = tuple(connection.execute(sa.text(
                "SELECT phase_l1, phase_l2, phase_l3, neutral, protective_earth "
                "FROM electrical_connections WHERE id='c2'"
            )).one())
            assert washer == (0, 1, 0)
            assert dryer == (0, 0, 1, 1, 1)

    print("Migration 0041: bestehende Phasenschienen-Verbindungen erfolgreich repariert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
