"""Verify migration 0045 creates phase-rail contacts for every DIN placement."""

from importlib import util
from pathlib import Path
import tempfile

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend/migrations/versions/0045_phase_rail_all_din_contacts.py"


def load():
    spec = util.spec_from_file_location("migration_0045", MIGRATION)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0045-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'test.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("""
                CREATE TABLE electrical_cabinet_components (
                    id TEXT PRIMARY KEY, distribution_id TEXT, area_id TEXT,
                    row_number INTEGER, start_position INTEGER, module_width INTEGER,
                    component_type TEXT, phase_l1 INTEGER, phase_l2 INTEGER,
                    phase_l3 INTEGER, start_phase TEXT, name TEXT, deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE asset_types (
                    id TEXT PRIMARY KEY, module_width INTEGER, deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE products (
                    id TEXT PRIMARY KEY, din_rail_mount INTEGER, module_width INTEGER,
                    deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE assets (
                    id TEXT PRIMARY KEY, name TEXT, asset_type_id TEXT, product_id TEXT,
                    module_width INTEGER, status TEXT, deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE electrical_components (
                    id TEXT PRIMARY KEY, asset_id TEXT, role TEXT, deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE electrical_protective_devices (
                    id TEXT PRIMARY KEY, distribution_id TEXT, area_id TEXT,
                    row_number INTEGER, start_position INTEGER, module_width INTEGER,
                    poles INTEGER, device_type TEXT
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE electrical_asset_placements (
                    id TEXT PRIMARY KEY, distribution_id TEXT, area_id TEXT, asset_id TEXT,
                    row_number INTEGER, start_position INTEGER, module_width INTEGER,
                    deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE electrical_connections (
                    id TEXT PRIMARY KEY, source_kind TEXT, source_id TEXT,
                    target_kind TEXT, target_id TEXT, connection_type TEXT, label TEXT,
                    phase_l1 INTEGER, phase_l2 INTEGER, phase_l3 INTEGER,
                    neutral INTEGER, protective_earth INTEGER, cable_type TEXT,
                    cores INTEGER, cross_section_mm2 REAL, length_m REAL,
                    route TEXT, notes TEXT, created_at DATETIME,
                    updated_at DATETIME, deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE smart_meter_measurement_points (
                    id TEXT PRIMARY KEY, connection_id TEXT, phase TEXT,
                    updated_at DATETIME, deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE smart_meter_measurement_entities (
                    id TEXT PRIMARY KEY, measurement_point_id TEXT
                )
            """)

            connection.exec_driver_sql(
                "INSERT INTO asset_types VALUES ('type', 1, NULL)"
            )
            for index, name in enumerate(("Keller", "Waschmaschine", "Trockner", "Stromstoßschalter"), 1):
                connection.execute(sa.text("""
                    INSERT INTO assets (id, name, asset_type_id, product_id, module_width, status, deleted_at)
                    VALUES (:id, :name, 'type', NULL, NULL, 'active', NULL)
                """), {"id": f"asset-{index}", "name": name})
                connection.execute(sa.text("""
                    INSERT INTO electrical_asset_placements
                    VALUES (:id, 'dist', 'area', :asset, 1, :position, 1, NULL)
                """), {"id": f"placement-{index}", "asset": f"asset-{index}", "position": index})

            connection.exec_driver_sql("""
                INSERT INTO electrical_cabinet_components
                VALUES ('rail-assets', 'dist', 'area', 1, 1, 10,
                        'phase_rail', 1, 1, 1, 'L1', 'Kammschiene', NULL)
            """)

            # Four-pole FI/RCD: first three rail contacts are L1/L2/L3; pole 4 is N.
            connection.exec_driver_sql("""
                INSERT INTO assets VALUES ('fi-asset', 'FI', 'type', NULL, 4, 'active', NULL)
            """)
            connection.exec_driver_sql("""
                INSERT INTO electrical_components VALUES ('fi-device', 'fi-asset', 'protective_device', NULL)
            """)
            connection.exec_driver_sql("""
                INSERT INTO electrical_protective_devices
                VALUES ('fi-device', 'dist', 'area', 2, 1, 4, 4, 'rcd')
            """)
            connection.exec_driver_sql("""
                INSERT INTO electrical_cabinet_components
                VALUES ('rail-fi', 'dist', 'area', 2, 1, 4,
                        'phase_rail', 1, 1, 1, 'L1', 'FI-Kammschiene', NULL)
            """)

            migration = load()
            migration.op = operations(connection)
            migration.upgrade()

            rows = connection.execute(sa.text("""
                SELECT source_id, target_kind, target_id, phase_l1, phase_l2, phase_l3,
                       neutral, protective_earth
                FROM electrical_connections
                WHERE deleted_at IS NULL
                ORDER BY source_id, target_kind, target_id
            """)).mappings().all()
            mapped = {
                (row["source_id"], row["target_kind"], row["target_id"]): (
                    row["phase_l1"], row["phase_l2"], row["phase_l3"],
                    row["neutral"], row["protective_earth"],
                )
                for row in rows
            }
            assert mapped[("rail-assets", "asset", "asset-1")] == (1, 0, 0, 0, 0)
            assert mapped[("rail-assets", "asset", "asset-2")] == (0, 1, 0, 0, 0)
            assert mapped[("rail-assets", "asset", "asset-3")] == (0, 0, 1, 0, 0)
            assert mapped[("rail-assets", "asset", "asset-4")] == (1, 0, 0, 0, 0)
            assert mapped[("rail-fi", "protective_device", "fi-device")] == (1, 1, 1, 0, 0)

            migration.upgrade()
            count = connection.execute(sa.text(
                "SELECT COUNT(*) FROM electrical_connections WHERE deleted_at IS NULL"
            )).scalar_one()
            assert count == 5, count

    print("Migration 0045: alle DIN-Geräte einschließlich FI-Sonderfall verkabelt.")


if __name__ == "__main__":
    main()
