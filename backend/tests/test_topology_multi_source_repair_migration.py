import importlib.util
import sqlite3
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa


MIGRATION_PATH = Path(__file__).parents[1] / "migrations" / "versions" / (
    "0033_remove_legacy_single_target_topology_index.py"
)
LEGACY_INDEX = "uq_electrical_connections_active_target"


def test_migration_0033_repairs_already_migrated_database(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE electrical_connections (
                id TEXT PRIMARY KEY,
                source_kind TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_kind TEXT NOT NULL,
                target_id TEXT NOT NULL,
                deleted_at DATETIME NULL
            );
            CREATE UNIQUE INDEX uq_electrical_connections_active_pair
            ON electrical_connections (
                source_kind, source_id, target_kind, target_id
            ) WHERE deleted_at IS NULL;
            CREATE UNIQUE INDEX uq_electrical_connections_active_target
            ON electrical_connections (target_kind, target_id)
            WHERE deleted_at IS NULL;
            """
        )

    spec = importlib.util.spec_from_file_location("migration_0033", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = sa.create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

    with sqlite3.connect(database_path) as connection:
        indexes = {
            row[1]
            for row in connection.execute(
                "PRAGMA index_list('electrical_connections')"
            ).fetchall()
        }
        assert LEGACY_INDEX not in indexes
        connection.execute(
            "INSERT INTO electrical_connections VALUES "
            "('one', 'asset', 'meter', 'cabinet_component', 'block', NULL)"
        )
        connection.execute(
            "INSERT INTO electrical_connections VALUES "
            "('two', 'asset', 'inverter', 'cabinet_component', 'block', NULL)"
        )
        connection.commit()
        assert connection.execute(
            "SELECT COUNT(*) FROM electrical_connections WHERE target_id = 'block'"
        ).fetchone() == (2,)
