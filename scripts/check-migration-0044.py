"""Verify late-created phase rails are reconciled by migration 0044."""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "backend/migrations/versions"


def load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Migration konnte nicht geladen werden: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operations(connection: sa.Connection) -> Operations:
    return Operations(MigrationContext.configure(connection))


def run_until(connection: sa.Connection, revision: str) -> None:
    for path in sorted(MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.py")):
        migration = load(path)
        migration.op = operations(connection)
        migration.upgrade()
        if migration.revision == revision:
            return
    raise AssertionError(f"Revision {revision} wurde nicht gefunden")


def main() -> int:
    now = "2026-07-28 07:00:00"
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0044-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'migration.sqlite3'}")
        with engine.begin() as connection:
            run_until(connection, "0043")
            connection.execute(sa.text("PRAGMA foreign_keys=OFF"))
            connection.execute(sa.text("""
                INSERT INTO electrical_cabinet_components (
                    id, distribution_id, area_id, component_type, name,
                    row_number, start_position, module_width,
                    phase_l1, phase_l2, phase_l3, neutral, protective_earth,
                    created_at, updated_at, deleted_at,
                    linked_rcd_device_id, start_phase, mounting_side
                ) VALUES (
                    'late-rail', 'dist', 'area', 'phase_rail', 'Kammschiene 1 OG',
                    1, 1, 10, 1, 1, 1, 0, 0, :now, :now, NULL,
                    NULL, 'L1', 'below'
                )
            """), {"now": now})
            connection.execute(sa.text("""
                INSERT INTO electrical_components (
                    id, asset_id, role, created_at, updated_at, deleted_at
                ) VALUES ('feed', 'asset-feed', 'protective_device', :now, :now, NULL)
            """), {"now": now})
            connection.execute(sa.text("""
                INSERT INTO electrical_protective_devices (
                    id, distribution_id, area_id, device_type, row_number,
                    start_position, module_width, poles
                ) VALUES ('feed', 'dist', 'area', 'mcb', 2, 1, 3, 3)
            """))
            connection.execute(sa.text("""
                INSERT INTO electrical_connections (
                    id, source_kind, source_id, target_kind, target_id,
                    connection_type, phase_l1, phase_l2, phase_l3,
                    neutral, protective_earth, created_at, updated_at, deleted_at
                ) VALUES (
                    'upstream-feed', 'protective_device', 'feed',
                    'cabinet_component', 'late-rail', 'wire',
                    1, 1, 1, 0, 0, :now, :now, NULL
                )
            """), {"now": now})

            for index, device_id in enumerate(("keller", "washer", "dryer"), start=1):
                connection.execute(sa.text("""
                    INSERT INTO electrical_components (
                        id, asset_id, role, created_at, updated_at, deleted_at
                    ) VALUES (:id, :asset, 'protective_device', :now, :now, NULL)
                """), {"id": device_id, "asset": f"asset-{device_id}", "now": now})
                connection.execute(sa.text("""
                    INSERT INTO electrical_protective_devices (
                        id, distribution_id, area_id, device_type, row_number,
                        start_position, module_width, poles
                    ) VALUES (:id, 'dist', 'area', 'mcb', 1, :position, 1, 1)
                """), {"id": device_id, "position": index})
                connection.execute(sa.text("""
                    INSERT INTO electrical_connections (
                        id, source_kind, source_id, target_kind, target_id,
                        connection_type, phase_l1, phase_l2, phase_l3,
                        neutral, protective_earth, created_at, updated_at, deleted_at
                    ) VALUES (
                        :link_id, 'cabinet_component', 'old-block',
                        'protective_device', :device_id, 'wire',
                        1, 0, 0, 0, 0, :now, :now, NULL
                    )
                """), {
                    "link_id": f"old-{device_id}",
                    "device_id": device_id,
                    "now": now,
                })

            migration = load(MIGRATIONS / "0044_reconcile_phase_rail_contacts.py")
            migration.op = operations(connection)
            migration.upgrade()

            rows = connection.execute(sa.text("""
                SELECT target_id, phase_l1, phase_l2, phase_l3
                FROM electrical_connections
                WHERE source_kind='cabinet_component'
                  AND source_id='late-rail'
                  AND target_kind='protective_device'
                  AND deleted_at IS NULL
                ORDER BY target_id
            """)).all()
            phases = {row.target_id: (row.phase_l1, row.phase_l2, row.phase_l3) for row in rows}
            assert phases == {
                "dryer": (0, 0, 1),
                "keller": (1, 0, 0),
                "washer": (0, 1, 0),
            }
            assert connection.execute(sa.text("""
                SELECT count(*) FROM electrical_connections
                WHERE id IN ('old-keller', 'old-washer', 'old-dryer')
                  AND deleted_at IS NOT NULL
            """)).scalar_one() == 3
            assert connection.execute(sa.text("""
                SELECT count(*) FROM electrical_connections
                WHERE id='upstream-feed' AND deleted_at IS NULL
            """)).scalar_one() == 1

            # The repair is intentionally idempotent.
            migration.upgrade()
            assert connection.execute(sa.text("""
                SELECT count(*) FROM electrical_connections
                WHERE source_id='late-rail' AND deleted_at IS NULL
            """)).scalar_one() == 3

    print("Migration 0044: spät angelegte Kammschiene automatisch verkabelt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
