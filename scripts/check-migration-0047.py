"""Verify migration 0047 adds FI/RCD Asset references to cabinet components."""

from importlib import util
from pathlib import Path
import tempfile

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend/migrations/versions/0047_link_cabinet_rails_to_din_rcd_assets.py"


def load():
    spec = util.spec_from_file_location("migration_0047", MIGRATION)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0047-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'test.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE assets (id CHAR(32) PRIMARY KEY)")
            connection.exec_driver_sql(
                "CREATE TABLE electrical_protective_devices (id CHAR(32) PRIMARY KEY)"
            )
            connection.exec_driver_sql("""
                CREATE TABLE electrical_cabinet_components (
                    id CHAR(32) PRIMARY KEY,
                    component_type VARCHAR(40) NOT NULL,
                    linked_rcd_device_id CHAR(32),
                    FOREIGN KEY(linked_rcd_device_id)
                        REFERENCES electrical_protective_devices(id)
                )
            """)
            migration = load()
            migration.op = operations(connection)
            migration.upgrade()

            inspector = sa.inspect(connection)
            columns = {item["name"] for item in inspector.get_columns(
                "electrical_cabinet_components"
            )}
            assert "linked_rcd_asset_id" in columns
            indexes = {item["name"] for item in inspector.get_indexes(
                "electrical_cabinet_components"
            )}
            assert "ix_electrical_cabinet_components_linked_rcd_asset_id" in indexes
            foreign_keys = inspector.get_foreign_keys("electrical_cabinet_components")
            assert any(
                fk["referred_table"] == "assets"
                and fk["constrained_columns"] == ["linked_rcd_asset_id"]
                for fk in foreign_keys
            )

            connection.exec_driver_sql(
                "INSERT INTO assets (id) VALUES ('asset-fi')"
            )
            connection.exec_driver_sql(
                "INSERT INTO electrical_cabinet_components "
                "(id, component_type, linked_rcd_asset_id) "
                "VALUES ('rail', 'phase_rail', 'asset-fi')"
            )

    print("Migration 0047: FI/RCD-DIN-Asset-Verweise ergänzt.")


if __name__ == "__main__":
    main()
