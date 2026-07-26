"""Exercise migration 0030 against a representative SQLite 0029 table."""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "backend" / "migrations" / "versions" / "0030_enable_subdistribution_sections.py"
)


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0030", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Migration 0030 konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def constraint_names(inspector: sa.Inspector) -> set[str]:
    return {
        constraint["name"]
        for constraint in inspector.get_check_constraints("electrical_distributions")
        if constraint.get("name")
    }


def operations(connection: sa.Connection) -> Operations:
    context = MigrationContext.configure(connection)
    return Operations(context)


def main() -> int:
    migration = load_migration()
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0030-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'migration.sqlite3'}")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE electrical_distributions ("
                "id VARCHAR(32) PRIMARY KEY, "
                "distribution_type VARCHAR(20) NOT NULL, "
                "layout_mode VARCHAR(20) NOT NULL, "
                "designation VARCHAR(200), "
                "CONSTRAINT ck_electrical_distributions_sub_rows_layout "
                "CHECK (distribution_type = 'main' OR layout_mode = 'rows')"
                ")"
            )
            connection.exec_driver_sql(
                "INSERT INTO electrical_distributions "
                "(id, distribution_type, layout_mode, designation) VALUES "
                "('main', 'main', 'sections', 'HV'), "
                "('sub', 'sub', 'rows', 'UV')"
            )

        with engine.begin() as connection:
            try:
                connection.exec_driver_sql(
                    "UPDATE electrical_distributions SET layout_mode='sections' WHERE id='sub'"
                )
            except IntegrityError:
                pass
            else:
                raise AssertionError(
                    "Die 0029-Prüfbedingung wurde vor dem Upgrade nicht erzwungen."
                )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()

        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE electrical_distributions SET layout_mode='sections' WHERE id='sub'"
            )
            assert (
                "ck_electrical_distributions_sub_rows_layout"
                not in constraint_names(sa.inspect(connection))
            )

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.downgrade()

        with engine.begin() as connection:
            assert connection.exec_driver_sql(
                "SELECT layout_mode FROM electrical_distributions WHERE id='sub'"
            ).scalar_one() == "rows"
            assert (
                "ck_electrical_distributions_sub_rows_layout"
                in constraint_names(sa.inspect(connection))
            )
            assert connection.exec_driver_sql(
                "SELECT designation FROM electrical_distributions WHERE id='sub'"
            ).scalar_one() == "UV"

        with engine.begin() as connection:
            migration.op = operations(connection)
            migration.upgrade()

        with engine.begin() as connection:
            assert (
                "ck_electrical_distributions_sub_rows_layout"
                not in constraint_names(sa.inspect(connection))
            )
            assert connection.exec_driver_sql(
                "SELECT designation FROM electrical_distributions WHERE id='sub'"
            ).scalar_one() == "UV"

    print("Migration 0030: Upgrade, Downgrade und erneutes Upgrade erfolgreich geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
