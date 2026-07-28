"""Verify migration 0049 materializes active N and PE layout areas."""

from importlib import util
from pathlib import Path
import tempfile

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend/migrations/versions/0049_materialize_n_pe_rail_endpoints.py"


def load():
    spec = util.spec_from_file_location("migration_0049", MIGRATION)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0049-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'test.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("""
                CREATE TABLE electrical_distributions (
                    id CHAR(32) PRIMARY KEY
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE electrical_distribution_sections (
                    id CHAR(32) PRIMARY KEY,
                    distribution_id CHAR(32) NOT NULL,
                    deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE electrical_distribution_areas (
                    id CHAR(32) PRIMARY KEY,
                    section_id CHAR(32) NOT NULL,
                    name VARCHAR(150) NOT NULL,
                    area_type VARCHAR(40) NOT NULL,
                    deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql("""
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
                    linked_rcd_device_id CHAR(32),
                    linked_rcd_asset_id CHAR(32),
                    start_phase VARCHAR(2),
                    mounting_side VARCHAR(10),
                    description TEXT,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                )
            """)
            connection.exec_driver_sql(
                "INSERT INTO electrical_distributions (id) VALUES ('dist')"
            )
            connection.exec_driver_sql(
                "INSERT INTO electrical_distribution_sections "
                "(id, distribution_id, deleted_at) VALUES ('section', 'dist', NULL)"
            )
            connection.exec_driver_sql("""
                INSERT INTO electrical_distribution_areas
                    (id, section_id, name, area_type, deleted_at)
                VALUES
                    ('n-area', 'section', 'N-Schiene FI 1', 'neutral_rail', NULL),
                    ('pe-area', 'section', 'PE-Schiene', 'protective_earth_rail', NULL),
                    ('reserve-area', 'section', 'Reserve', 'reserve', NULL)
            """)

            migration = load()
            migration.op = operations(connection)
            migration.upgrade()

            rows = connection.execute(sa.text("""
                SELECT area_id, component_type, name, neutral, protective_earth
                FROM electrical_cabinet_components
                ORDER BY area_id
            """)).mappings().all()
            assert len(rows) == 2
            by_area = {row["area_id"]: row for row in rows}
            assert by_area["n-area"]["component_type"] == "neutral_rail"
            assert by_area["n-area"]["neutral"] == 1
            assert by_area["n-area"]["protective_earth"] == 0
            assert by_area["pe-area"]["component_type"] == "protective_earth_rail"
            assert by_area["pe-area"]["neutral"] == 0
            assert by_area["pe-area"]["protective_earth"] == 1

            migration.upgrade()
            count = connection.execute(sa.text(
                "SELECT COUNT(*) FROM electrical_cabinet_components"
            )).scalar_one()
            assert count == 2

            migration.downgrade()
            count_after_downgrade = connection.execute(sa.text(
                "SELECT COUNT(*) FROM electrical_cabinet_components"
            )).scalar_one()
            assert count_after_downgrade == 2

    print("Migration 0049: N-/PE-Schienenbereiche materialisiert und idempotent geprüft.")


if __name__ == "__main__":
    main()
