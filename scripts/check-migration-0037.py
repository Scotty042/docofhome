"""Exercise migration 0037 against a minimal SQLite 0036-style schema."""

from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "backend/migrations/versions/0037_release_1_6_electrical_measurements.py"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0037", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0037 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def table_names(connection: sa.Connection) -> set[str]:
    return set(sa.inspect(connection).get_table_names())


def columns(connection: sa.Connection, table: str) -> set[str]:
    return {str(item["name"]) for item in sa.inspect(connection).get_columns(table)}


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0037-") as directory:
        path = Path(directory) / "migration.sqlite3"
        timestamp = "2026-07-27 12:00:00"
        asset_type_id = uuid4().hex
        smart_meter_id = uuid4().hex
        source_id = uuid4().hex
        target_id = uuid4().hex
        connection_id = uuid4().hex
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE asset_types (
                    id CHAR(32) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                );
                CREATE TABLE assets (
                    id CHAR(32) PRIMARY KEY,
                    asset_type_id CHAR(32) NOT NULL,
                    name VARCHAR(150) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME,
                    FOREIGN KEY(asset_type_id) REFERENCES asset_types(id)
                );
                CREATE TABLE electrical_connections (
                    id CHAR(32) PRIMARY KEY,
                    source_kind VARCHAR(30) NOT NULL,
                    source_id CHAR(32) NOT NULL,
                    target_kind VARCHAR(30) NOT NULL,
                    target_id CHAR(32) NOT NULL,
                    connection_type VARCHAR(30) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                );
                """
            )
            connection.execute(
                "INSERT INTO asset_types VALUES (?, 'Smart Meter', ?, ?, NULL)",
                (asset_type_id, timestamp, timestamp),
            )
            for asset_id, name in (
                (smart_meter_id, "Smart Meter"),
                (source_id, "Zähler"),
                (target_id, "Hauptschalter"),
            ):
                connection.execute(
                    "INSERT INTO assets VALUES (?, ?, ?, ?, ?, NULL)",
                    (asset_id, asset_type_id, name, timestamp, timestamp),
                )
            connection.execute(
                "INSERT INTO electrical_connections VALUES "
                "(?, 'asset', ?, 'asset', ?, 'cable', ?, ?, NULL)",
                (connection_id, source_id, target_id, timestamp, timestamp),
            )
            connection.commit()

        engine = sa.create_engine(f"sqlite:///{path}")
        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            expected_asset_columns = {
                "breaker_characteristic",
                "rated_current_a",
                "coil_voltage_v",
                "coil_voltage_type",
                "contact_count",
                "contact_type",
            }
            assert expected_asset_columns <= columns(connection, "asset_types")
            assert expected_asset_columns <= columns(connection, "assets")
            assert {
                "smart_meter_measurement_points",
                "smart_meter_measurement_entities",
            } <= table_names(connection)
            point_id = uuid4().hex
            connection.execute(
                sa.text(
                    "INSERT INTO smart_meter_measurement_points "
                    "(id, smart_meter_asset_id, connection_id, channel_name, name, phase, "
                    "direction, inverted, created_at, updated_at) "
                    "VALUES (:id, :asset, :connection, 'CT1', 'Hausanschluss L1', 'L1', "
                    "'source_to_target', 0, :created, :updated)"
                ),
                {
                    "id": point_id,
                    "asset": smart_meter_id,
                    "connection": connection_id,
                    "created": timestamp,
                    "updated": timestamp,
                },
            )
            connection.execute(
                sa.text(
                    "INSERT INTO smart_meter_measurement_entities "
                    "(id, measurement_point_id, entity_id, role, created_at, updated_at) "
                    "VALUES (:id, :point, 'sensor.smart_meter_l1_power', 'power', "
                    ":created, :updated)"
                ),
                {
                    "id": uuid4().hex,
                    "point": point_id,
                    "created": timestamp,
                    "updated": timestamp,
                },
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()
            assert "smart_meter_measurement_points" not in table_names(connection)
            assert "breaker_characteristic" not in columns(connection, "assets")
            assert "coil_voltage_v" not in columns(connection, "assets")
            assert "rated_current_a" not in columns(connection, "asset_types")
            assert "contact_type" not in columns(connection, "asset_types")

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()
            assert "smart_meter_measurement_entities" in table_names(connection)

    print("Migration 0037: Upgrade, Downgrade und erneutes Upgrade erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
