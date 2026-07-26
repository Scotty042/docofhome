import importlib.util
import sqlite3
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa


MIGRATION_PATH = Path(__file__).parents[1] / "migrations" / "versions" / (
    "0034_home_electrical_groups.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0034", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _create_previous_schema(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE electrical_components (id CHAR(32) PRIMARY KEY);
            CREATE TABLE electrical_distributions (id CHAR(32) PRIMARY KEY);
            CREATE TABLE electrical_distribution_areas (id CHAR(32) PRIMARY KEY);
            CREATE TABLE electrical_cabinet_components (
                id CHAR(32) PRIMARY KEY,
                distribution_id CHAR(32) NOT NULL,
                area_id CHAR(32),
                component_type VARCHAR(40) NOT NULL,
                name VARCHAR(150) NOT NULL,
                row_number INTEGER NOT NULL,
                start_position INTEGER NOT NULL,
                module_width INTEGER NOT NULL,
                phase_l1 BOOLEAN NOT NULL DEFAULT 0,
                phase_l2 BOOLEAN NOT NULL DEFAULT 0,
                phase_l3 BOOLEAN NOT NULL DEFAULT 0,
                neutral BOOLEAN NOT NULL DEFAULT 0,
                protective_earth BOOLEAN NOT NULL DEFAULT 0,
                rated_current_a FLOAT,
                max_cross_section_mm2 FLOAT,
                outgoing_connections INTEGER,
                description TEXT,
                notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                deleted_at DATETIME
            );
            CREATE TABLE electrical_protective_devices (
                id CHAR(32) PRIMARY KEY,
                distribution_id CHAR(32) NOT NULL,
                area_id CHAR(32),
                device_type VARCHAR(20) NOT NULL,
                row_number INTEGER,
                start_position INTEGER,
                module_width INTEGER,
                rated_current_a FLOAT,
                residual_current_ma FLOAT,
                characteristic VARCHAR(30),
                poles INTEGER,
                breaking_capacity_ka FLOAT,
                rcd_type VARCHAR(80),
                fuse_type VARCHAR(80),
                spd_type VARCHAR(80),
                description TEXT,
                notes TEXT
            );
            """
        )


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info('{table}')")}


def test_migration_0034_upgrades_and_downgrades_sqlite(tmp_path: Path) -> None:
    database_path = tmp_path / "electrical-groups.sqlite3"
    _create_previous_schema(database_path)
    migration = _load_migration()
    engine = sa.create_engine(f"sqlite:///{database_path}")

    with engine.begin() as connection:
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

    with sqlite3.connect(database_path) as connection:
        assert {"linked_rcd_device_id", "start_phase"} <= _columns(
            connection, "electrical_cabinet_components"
        )
        assert {"assigned_rcd_id", "neutral_rail_id"} <= _columns(
            connection, "electrical_protective_devices"
        )
        cabinet_targets = {
            row[2]
            for row in connection.execute(
                "PRAGMA foreign_key_list('electrical_cabinet_components')"
            )
        }
        device_targets = {
            row[2]
            for row in connection.execute(
                "PRAGMA foreign_key_list('electrical_protective_devices')"
            )
        }
        assert "electrical_protective_devices" in cabinet_targets
        assert {"electrical_protective_devices", "electrical_cabinet_components"} <= device_targets

    with engine.begin() as connection:
        migration.op = Operations(MigrationContext.configure(connection))
        migration.downgrade()

    with sqlite3.connect(database_path) as connection:
        assert "linked_rcd_device_id" not in _columns(
            connection, "electrical_cabinet_components"
        )
        assert "assigned_rcd_id" not in _columns(
            connection, "electrical_protective_devices"
        )
