"""Verify migration 0046 repairs missing and stale asset code counters."""

from importlib import util
from pathlib import Path
import tempfile

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend/migrations/versions/0046_repair_asset_code_counters.py"


def load():
    spec = util.spec_from_file_location("migration_0046", MIGRATION)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0046-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'test.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql("""
                CREATE TABLE asset_types (
                    id TEXT PRIMARY KEY, code_prefix TEXT NOT NULL
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE assets (
                    id TEXT PRIMARY KEY, jarvis_code TEXT NOT NULL
                )
            """)
            connection.exec_driver_sql("""
                CREATE TABLE asset_code_counters (
                    prefix TEXT PRIMARY KEY, next_value INTEGER NOT NULL
                )
            """)
            connection.exec_driver_sql(
                "INSERT INTO asset_types VALUES ('relay', 'SRA'), ('meter', 'MET'), ('empty', 'EMP')"
            )
            connection.exec_driver_sql(
                "INSERT INTO assets VALUES ('a', 'SRA-001'), ('b', 'SRA-007'), ('c', 'MET-004')"
            )
            connection.exec_driver_sql(
                "INSERT INTO asset_code_counters VALUES ('MET', 2)"
            )

            migration = load()
            migration.op = operations(connection)
            migration.upgrade()

            counters = dict(connection.execute(sa.text(
                "SELECT prefix, next_value FROM asset_code_counters ORDER BY prefix"
            )).all())
            assert counters == {"EMP": 1, "MET": 5, "SRA": 8}, counters

            migration.upgrade()
            counters_again = dict(connection.execute(sa.text(
                "SELECT prefix, next_value FROM asset_code_counters ORDER BY prefix"
            )).all())
            assert counters_again == counters

    print("Migration 0046: fehlende und veraltete Asset-Codezähler repariert.")


if __name__ == "__main__":
    main()
