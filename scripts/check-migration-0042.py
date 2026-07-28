"""Exercise migration 0042 against a minimal SQLite 0041-style schema."""

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
MIGRATION_PATH = ROOT / "backend/migrations/versions/0042_auto_phase_rail_connections.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0042", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0042 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0042-") as directory:
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
                    connection_type TEXT NOT NULL,
                    label TEXT,
                    phase_l1 BOOLEAN NOT NULL,
                    phase_l2 BOOLEAN NOT NULL,
                    phase_l3 BOOLEAN NOT NULL,
                    neutral BOOLEAN NOT NULL,
                    protective_earth BOOLEAN NOT NULL,
                    cable_type TEXT,
                    cores INTEGER,
                    cross_section_mm2 FLOAT,
                    length_m FLOAT,
                    route TEXT,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                );

                INSERT INTO electrical_cabinet_components VALUES
                    ('rail', 'dist', NULL, 'phase_rail', 1, 1, 6, 1, 1, 1, 'L1', NULL);
                INSERT INTO electrical_components VALUES
                    ('cellar', NULL), ('washer', NULL);
                INSERT INTO electrical_protective_devices VALUES
                    ('cellar', 'dist', NULL, 1, 1, 1),
                    ('washer', 'dist', NULL, 1, 2, 1);
                INSERT INTO electrical_connections VALUES
                    ('existing', 'cabinet_component', 'rail', 'protective_device', 'cellar',
                     'busbar', NULL, 0, 1, 0, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL,
                     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL),
                    ('reverse', 'protective_device', 'washer', 'cabinet_component', 'rail',
                     'busbar', NULL, 0, 0, 1, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL,
                     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL);
                """
            )
            connection.commit()

        engine = sa.create_engine(f"sqlite:///{path}")
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            cellar = tuple(
                connection.execute(
                    sa.text(
                        "SELECT phase_l1, phase_l2, phase_l3, neutral, protective_earth "
                        "FROM electrical_connections WHERE id='existing'"
                    )
                ).one()
            )
            washer = tuple(
                connection.execute(
                    sa.text(
                        "SELECT phase_l1, phase_l2, phase_l3, connection_type "
                        "FROM electrical_connections "
                        "WHERE source_id='rail' AND target_id='washer' AND deleted_at IS NULL"
                    )
                ).one()
            )
            reverse_deleted = connection.execute(
                sa.text("SELECT deleted_at FROM electrical_connections WHERE id='reverse'")
            ).scalar_one()
            assert cellar == (1, 0, 0, 0, 0)
            assert washer == (0, 1, 0, "busbar")
            assert reverse_deleted is not None

    print("Migration 0042: automatische Phasenschienen-Verbindungen erfolgreich geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
