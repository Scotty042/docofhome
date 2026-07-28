"""Exercise migration 0048 against a minimal pre-1.7 SQLite schema."""
from __future__ import annotations

from importlib import util
from pathlib import Path
import tempfile
from uuid import uuid4

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend/migrations/versions/0048_release_1_7_1.py"


def load():
    spec = util.spec_from_file_location("migration_0048", MIGRATION)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0048-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'test.sqlite3'}")
        metadata = sa.MetaData()
        sa.Table(
            "asset_types",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
        )
        sa.Table(
            "assets",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
        )
        sa.Table(
            "network_interfaces",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("speed_mbps", sa.Integer()),
            sa.CheckConstraint(
                "speed_mbps IS NULL OR (speed_mbps >= 1 AND speed_mbps <= 1000000)",
                name="ck_network_interfaces_speed",
            ),
        )
        sa.Table(
            "network_addresses",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("address", sa.String(64), nullable=False),
        )
        sa.Table(
            "electrical_cabinet_components",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("component_type", sa.String(50), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
        )
        sa.Table(
            "electrical_circuits",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("protective_device_id", sa.Uuid(), nullable=True),
        )
        sa.Table(
            "electrical_connections",
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("source_kind", sa.String(40), nullable=False),
            sa.Column("source_id", sa.Uuid(), nullable=False),
            sa.Column("connection_type", sa.String(20), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
        )
        metadata.create_all(engine)

        meter_id, regular_id = uuid4(), uuid4()
        wire_id, rail_id, stale_busbar_id = uuid4(), uuid4(), uuid4()
        rail_component, plain_component = uuid4(), uuid4()
        with engine.begin() as connection:
            connection.execute(sa.text(
                "INSERT INTO asset_types (id, name) VALUES (:id, 'Stromzähler')"
            ), {"id": meter_id.hex})
            connection.execute(sa.text(
                "INSERT INTO asset_types (id, name) VALUES (:id, 'Switch')"
            ), {"id": regular_id.hex})
            connection.execute(sa.text(
                "INSERT INTO electrical_cabinet_components (id, component_type, deleted_at) "
                "VALUES (:id, 'phase_rail', NULL), (:other, 'terminal_block', NULL)"
            ), {"id": rail_component.hex, "other": plain_component.hex})
            for connection_id, source_id, kind in (
                (wire_id, plain_component, "wire"),
                (rail_id, rail_component, "busbar"),
                (stale_busbar_id, plain_component, "busbar"),
            ):
                connection.execute(sa.text(
                    "INSERT INTO electrical_connections "
                    "(id, source_kind, source_id, connection_type, deleted_at) "
                    "VALUES (:id, 'cabinet_component', :source, :kind, NULL)"
                ), {"id": connection_id.hex, "source": source_id.hex, "kind": kind})

            migration = load()
            migration.op = operations(connection)
            migration.upgrade()

            inspector = sa.inspect(connection)
            assert {"image_url", "image_source", "image_reference", "is_meter", "switch_port_layout"}.issubset(
                {column["name"] for column in inspector.get_columns("asset_types")}
            )
            assert {"image_url", "image_source", "image_reference"}.issubset(
                {column["name"] for column in inspector.get_columns("assets")}
            )
            assert {"phase_source", "source_connection_id"}.issubset(
                {column["name"] for column in inspector.get_columns("electrical_connections")}
            )
            assert "protective_device_asset_id" in {
                column["name"] for column in inspector.get_columns("electrical_circuits")
            }
            assert "network_observed_addresses" in inspector.get_table_names()
            assert "network_address_changes" in inspector.get_table_names()

            meter_rows = connection.execute(sa.text(
                "SELECT name, is_meter FROM asset_types ORDER BY name"
            )).mappings().all()
            assert {row["name"]: row["is_meter"] for row in meter_rows} == {
                "Stromzähler": 1,
                "Switch": 0,
            }
            phase_rows = connection.execute(sa.text(
                "SELECT id, phase_source, source_connection_id FROM electrical_connections"
            )).mappings().all()
            phases = {str(row["id"]): (row["phase_source"], str(row["source_connection_id"])) for row in phase_rows}
            assert phases[wire_id.hex] == ("wire", wire_id.hex)
            assert phases[rail_id.hex] == ("busbar", rail_id.hex)
            assert phases[stale_busbar_id.hex][0] == "manual"

            speed_checks = {item["name"]: item["sqltext"] for item in inspector.get_check_constraints("network_interfaces")}
            assert "IN (100, 1000, 2500)" in speed_checks["ck_network_interfaces_speed"]

            migration.downgrade()
            inspector = sa.inspect(connection)
            assert "network_observed_addresses" not in inspector.get_table_names()
            assert "network_address_changes" not in inspector.get_table_names()
            asset_type_columns = {column["name"] for column in inspector.get_columns("asset_types")}
            assert "is_meter" not in asset_type_columns
            assert "switch_port_layout" not in asset_type_columns
            assert "phase_source" not in {column["name"] for column in inspector.get_columns("electrical_connections")}
            assert "protective_device_asset_id" not in {
                column["name"] for column in inspector.get_columns("electrical_circuits")
            }

    print("Migration 0048: Schema, Zähler-Backfill und Phasenquellen erfolgreich geprüft.")


if __name__ == "__main__":
    main()
