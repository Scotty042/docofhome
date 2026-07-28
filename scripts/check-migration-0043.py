"""Exercise the complete migration chain and 1.6.3 electrical repairs."""

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
    now = "2026-07-27 12:00:00"
    with tempfile.TemporaryDirectory(prefix="docofhome-migration-0043-") as directory:
        engine = sa.create_engine(f"sqlite:///{Path(directory) / 'migration.sqlite3'}")
        with engine.begin() as connection:
            run_until(connection, "0042")
            connection.execute(sa.text("PRAGMA foreign_keys=OFF"))
            connection.execute(sa.text("""
                INSERT INTO electrical_cabinet_components (
                    id, distribution_id, area_id, component_type, name,
                    row_number, start_position, module_width,
                    phase_l1, phase_l2, phase_l3, neutral, protective_earth,
                    created_at, updated_at, deleted_at,
                    linked_rcd_device_id, start_phase, mounting_side
                ) VALUES
                    ('rail', 'dist', NULL, 'phase_rail', 'Kammschiene',
                     1, 1, 4, 1, 1, 1, 1, 1, :now, :now, NULL,
                     'rcd', 'L1', NULL),
                    ('partial', 'dist', NULL, 'phase_rail', 'Kurze Schiene',
                     2, 1, 4, 1, 1, 1, 0, 0, :now, :now, NULL,
                     NULL, 'L1', 'below'),
                    ('neutral', 'dist', NULL, 'neutral_rail', 'N',
                     1, 1, 4, 1, 0, 0, 0, 1, :now, :now, NULL,
                     NULL, NULL, NULL),
                    ('pe', 'dist', NULL, 'protective_earth_rail', 'PE',
                     1, 1, 4, 1, 1, 0, 1, 0, :now, :now, NULL,
                     'rcd', NULL, NULL),
                    ('busbar', 'dist', NULL, 'busbar', 'Allgemeine Sammelschiene',
                     2, 6, 3, 1, 1, 1, 0, 0, :now, :now, NULL,
                     'rcd', 'L2', 'above')
            """), {"now": now})
            for device_id in ("rcd", "washer", "dryer", "rcbo", "wide"):
                connection.execute(sa.text("""
                    INSERT INTO electrical_components (
                        id, asset_id, role, created_at, updated_at, deleted_at
                    ) VALUES (:id, :asset, 'protective_device', :now, :now, NULL)
                """), {"id": device_id, "asset": f"asset-{device_id}", "now": now})
            devices = [
                ("rcd", "rcd", 1, 1, 4, 4),
                ("washer", "mcb", 1, 2, 1, 1),
                ("dryer", "mcb", 1, 3, 1, 1),
                ("rcbo", "rcbo", 1, 4, 1, 2),
                ("wide", "mcb", 2, 4, 2, 1),
            ]
            for device_id, device_type, row, start, width, poles in devices:
                connection.execute(sa.text("""
                    INSERT INTO electrical_protective_devices (
                        id, distribution_id, device_type, row_number,
                        start_position, module_width, poles, area_id
                    ) VALUES (:id, 'dist', :device_type, :row, :start, :width, :poles, NULL)
                """), {
                    "id": device_id,
                    "device_type": device_type,
                    "row": row,
                    "start": start,
                    "width": width,
                    "poles": poles,
                })
            connection.execute(sa.text("""
                INSERT INTO electrical_circuits (
                    id, distribution_id, protective_device_id, name,
                    circuit_number, description, notes,
                    created_at, updated_at, deleted_at
                ) VALUES (
                    'circuit', 'dist', 'washer', 'Waschküche',
                    'F2', NULL, NULL, :now, :now, NULL
                )
            """), {"now": now})
            connection.execute(sa.text("""
                INSERT INTO electrical_connections (
                    id, source_kind, source_id, target_kind, target_id,
                    connection_type, phase_l1, phase_l2, phase_l3,
                    neutral, protective_earth, created_at, updated_at, deleted_at
                ) VALUES
                    ('wrong-washer', 'cabinet_component', 'rail',
                     'protective_device', 'washer', 'wire', 0, 0, 1, 1, 1,
                     :now, :now, NULL),
                    ('reverse', 'protective_device', 'dryer',
                     'cabinet_component', 'rail', 'busbar', 1, 0, 0, 0, 0,
                     :now, :now, NULL),
                    ('upstream-rcd', 'protective_device', 'rcd',
                     'cabinet_component', 'rail', 'busbar', 1, 1, 1, 0, 0,
                     :now, :now, NULL),
                    ('competing', 'asset', 'upstream',
                     'protective_device', 'dryer', 'wire', 1, 0, 0, 0, 0,
                     :now, :now, NULL),
                    ('downstream', 'protective_device', 'washer',
                     'asset', 'washing-machine', 'wire', 0, 0, 1, 1, 1,
                     :now, :now, NULL),
                    ('partial-link', 'cabinet_component', 'partial',
                     'protective_device', 'wide', 'busbar', 1, 0, 0, 0, 0,
                     :now, :now, NULL),
                    ('generic-single', 'asset', 'generic-source',
                     'asset', 'generic-target', 'wire', 0, 1, 0, 1, 1,
                     :now, :now, NULL),
                    ('circuit-in', 'protective_device', 'washer',
                     'circuit', 'circuit', 'wire', 1, 0, 0, 1, 1,
                     :now, :now, NULL),
                    ('circuit-out', 'circuit', 'circuit',
                     'asset', 'washer-load', 'cable', 1, 0, 0, 1, 1,
                     :now, :now, NULL)
            """), {"now": now})
            connection.execute(sa.text("""
                INSERT INTO smart_meter_measurement_points (
                    id, smart_meter_asset_id, connection_id, channel_name,
                    name, phase, direction, inverted, created_at, updated_at, deleted_at
                ) VALUES
                    ('point-competing', 'smart', 'competing', 'A', 'Trockner',
                     'L1', 'source_to_target', 0, :now, :now, NULL),
                    ('point-downstream', 'smart', 'downstream', 'B', 'Waschmaschine',
                     'L3', 'source_to_target', 0, :now, :now, NULL),
                    ('point-partial', 'smart', 'partial-link', 'C', 'Teilüberdeckung',
                     'L1', 'source_to_target', 0, :now, :now, NULL),
                    ('point-generic', 'smart', 'generic-single', 'D', 'Einphasig',
                     'L3', 'source_to_target', 0, :now, :now, NULL),
                    ('point-circuit', 'smart', 'circuit-out', 'E', 'Stromkreis',
                     'L1', 'source_to_target', 0, :now, :now, NULL)
            """), {"now": now})
            connection.execute(sa.text("""
                INSERT INTO smart_meter_measurement_entities (
                    id, measurement_point_id, entity_id, role, created_at, updated_at
                ) VALUES ('entity-partial', 'point-partial', 'sensor.partial', 'power', :now, :now)
            """), {"now": now})

            migration = load(MIGRATIONS / "0043_release_1_6_3_electrical_integrity.py")
            migration.op = operations(connection)
            migration.upgrade()

            links = {
                (row.source_id, row.target_id): (row.phase_l1, row.phase_l2, row.phase_l3)
                for row in connection.execute(sa.text("""
                    SELECT source_id, target_id, phase_l1, phase_l2, phase_l3
                    FROM electrical_connections
                    WHERE source_kind='cabinet_component'
                      AND target_kind='protective_device'
                      AND deleted_at IS NULL
                """)).all()
            }
            assert ("rail", "rcd") not in links
            assert links[("rail", "washer")] == (0, 1, 0)
            assert links[("rail", "dryer")] == (0, 0, 1)
            assert links[("rail", "rcbo")] == (1, 0, 0)
            assert ("partial", "wide") not in links
            assert connection.execute(
                sa.text("SELECT deleted_at FROM electrical_connections WHERE id='reverse'")
            ).scalar_one() is not None
            assert connection.execute(
                sa.text("SELECT deleted_at FROM electrical_connections WHERE id='upstream-rcd'")
            ).scalar_one() is None
            assert connection.execute(
                sa.text("SELECT deleted_at FROM electrical_connections WHERE id='competing'")
            ).scalar_one() is not None
            dryer_auto_id = connection.execute(sa.text("""
                SELECT id FROM electrical_connections
                WHERE source_id='rail' AND target_id='dryer' AND deleted_at IS NULL
            """)).scalar_one()
            assert connection.execute(sa.text("""
                SELECT connection_id, phase FROM smart_meter_measurement_points
                WHERE id='point-competing'
            """)).one() == (dryer_auto_id, "L3")
            assert connection.execute(sa.text("""
                SELECT phase_l1, phase_l2, phase_l3
                FROM electrical_connections WHERE id='downstream'
            """)).one() == (0, 1, 0)
            assert connection.execute(sa.text("""
                SELECT phase FROM smart_meter_measurement_points WHERE id='point-downstream'
            """)).scalar_one() == "L2"
            assert connection.execute(sa.text("""
                SELECT deleted_at FROM smart_meter_measurement_points WHERE id='point-partial'
            """)).scalar_one() is not None
            assert connection.execute(sa.text("""
                SELECT count(*) FROM smart_meter_measurement_entities
                WHERE measurement_point_id='point-partial'
            """)).scalar_one() == 0
            assert connection.execute(sa.text("""
                SELECT phase FROM smart_meter_measurement_points
                WHERE id='point-generic'
            """)).scalar_one() == "L2"
            assert connection.execute(sa.text("""
                SELECT phase_l1, phase_l2, phase_l3
                FROM electrical_connections WHERE id='circuit-in'
            """)).one() == (0, 1, 0)
            assert connection.execute(sa.text("""
                SELECT phase_l1, phase_l2, phase_l3
                FROM electrical_connections WHERE id='circuit-out'
            """)).one() == (0, 1, 0)
            assert connection.execute(sa.text("""
                SELECT phase FROM smart_meter_measurement_points
                WHERE id='point-circuit'
            """)).scalar_one() == "L2"

            rail = connection.execute(sa.text("""
                SELECT neutral, protective_earth, start_phase, mounting_side
                FROM electrical_cabinet_components WHERE id='rail'
            """)).one()
            neutral = connection.execute(sa.text("""
                SELECT phase_l1, neutral, protective_earth
                FROM electrical_cabinet_components WHERE id='neutral'
            """)).one()
            pe = connection.execute(sa.text("""
                SELECT phase_l1, phase_l2, neutral, protective_earth,
                       linked_rcd_device_id
                FROM electrical_cabinet_components WHERE id='pe'
            """)).one()
            busbar = connection.execute(sa.text("""
                SELECT linked_rcd_device_id, start_phase, mounting_side
                FROM electrical_cabinet_components WHERE id='busbar'
            """)).one()
            assert rail == (0, 0, "L1", "below")
            assert neutral == (0, 1, 0)
            assert pe == (0, 0, 0, 1, None)
            assert busbar == (None, None, None)

            try:
                connection.execute(sa.text("""
                    UPDATE electrical_cabinet_components
                    SET phase_l1=1, protective_earth=0
                    WHERE id='pe'
                """))
            except sa.exc.IntegrityError:
                pass
            else:
                raise AssertionError("PE-Leiter-Constraint wurde nicht erzwungen")

            try:
                connection.execute(sa.text("""
                    UPDATE electrical_cabinet_components
                    SET linked_rcd_device_id='rcd'
                    WHERE id='busbar'
                """))
            except sa.exc.IntegrityError:
                pass
            else:
                raise AssertionError("FI-Link-Constraint für allgemeine Sammelschiene fehlt")

            try:
                connection.execute(sa.text("""
                    UPDATE electrical_cabinet_components
                    SET start_phase='L1', mounting_side='below'
                    WHERE id='busbar'
                """))
            except sa.exc.IntegrityError:
                pass
            else:
                raise AssertionError("Phasenmetadaten-Constraint für Sammelschiene fehlt")

    print("Migration 0043: Elektro-Beziehungen und automatische Schienenlogik geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
