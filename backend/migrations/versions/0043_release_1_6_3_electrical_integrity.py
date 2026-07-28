"""Harden electrical placement, rail conductors and derived wiring.

Revision ID: 0043
Revises: 0042
Create Date: 2026-07-27
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LINE_PHASES = ("L1", "L2", "L3")


def _key(value: object | None) -> str | None:
    return None if value is None else str(value)


def _pattern(rail: dict[str, object]) -> list[str]:
    enabled = [
        phase
        for phase, column in (("L1", "phase_l1"), ("L2", "phase_l2"), ("L3", "phase_l3"))
        if bool(rail[column])
    ]
    if not enabled:
        return []
    start = str(rail.get("start_phase") or enabled[0])
    if start not in enabled:
        start = enabled[0]
    index = LINE_PHASES.index(start)
    rotated = LINE_PHASES[index:] + LINE_PHASES[:index]
    return [phase for phase in rotated if phase in enabled]


def _active_line_count(device_type: object, poles: object) -> int:
    count = max(1, int(poles or 1))
    if str(device_type) in {"rcd", "rcbo", "spd"} and count in {2, 4}:
        count -= 1
    return min(3, count)


def _normalize_components(connection: sa.Connection) -> None:
    connection.execute(sa.text("""
        UPDATE electrical_cabinet_components
        SET neutral=0, protective_earth=0,
            phase_l1=CASE
                WHEN phase_l1=0 AND phase_l2=0 AND phase_l3=0 THEN 1
                ELSE phase_l1
            END,
            start_phase=CASE
                WHEN start_phase='L1' AND phase_l1=1 THEN 'L1'
                WHEN start_phase='L2' AND phase_l2=1 THEN 'L2'
                WHEN start_phase='L3' AND phase_l3=1 THEN 'L3'
                WHEN phase_l1=1 THEN 'L1'
                WHEN phase_l2=1 THEN 'L2'
                ELSE 'L3'
            END,
            mounting_side=COALESCE(mounting_side, 'below')
        WHERE component_type='phase_rail'
    """))
    connection.execute(sa.text("""
        UPDATE electrical_cabinet_components
        SET phase_l1=0, phase_l2=0, phase_l3=0,
            neutral=1, protective_earth=0,
            start_phase=NULL, mounting_side=NULL
        WHERE component_type='neutral_rail'
    """))
    connection.execute(sa.text("""
        UPDATE electrical_cabinet_components
        SET phase_l1=0, phase_l2=0, phase_l3=0,
            neutral=0, protective_earth=1,
            linked_rcd_device_id=NULL,
            start_phase=NULL, mounting_side=NULL
        WHERE component_type='protective_earth_rail'
    """))
    connection.execute(sa.text("""
        UPDATE electrical_cabinet_components
        SET linked_rcd_device_id=NULL
        WHERE component_type NOT IN ('phase_rail', 'neutral_rail')
    """))
    connection.execute(sa.text("""
        UPDATE electrical_cabinet_components
        SET start_phase=NULL, mounting_side=NULL
        WHERE component_type!='phase_rail'
    """))


def _archive_connection(
    connection: sa.Connection,
    link_id: object,
    now: datetime,
    *,
    replacement_id: object | None = None,
) -> None:
    if replacement_id is not None:
        connection.execute(sa.text("""
            UPDATE smart_meter_measurement_points
            SET connection_id=:replacement_id, updated_at=:now
            WHERE connection_id=:link_id AND deleted_at IS NULL
        """), {
            "replacement_id": replacement_id,
            "link_id": link_id,
            "now": now,
        })
    else:
        point_ids = [
            row["id"]
            for row in connection.execute(sa.text("""
                SELECT id FROM smart_meter_measurement_points
                WHERE connection_id=:link_id AND deleted_at IS NULL
            """), {"link_id": link_id}).mappings()
        ]
        for point_id in point_ids:
            connection.execute(sa.text("""
                DELETE FROM smart_meter_measurement_entities
                WHERE measurement_point_id=:point_id
            """), {"point_id": point_id})
        connection.execute(sa.text("""
            UPDATE smart_meter_measurement_points
            SET deleted_at=:now, updated_at=:now
            WHERE connection_id=:link_id AND deleted_at IS NULL
        """), {"link_id": link_id, "now": now})
    connection.execute(sa.text("""
        UPDATE electrical_connections
        SET deleted_at=:now, updated_at=:now
        WHERE id=:link_id AND deleted_at IS NULL
    """), {"link_id": link_id, "now": now})


def _repair_derived_connections(connection: sa.Connection) -> None:
    now = datetime.now(UTC)
    rails = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT id, distribution_id, area_id, row_number, start_position,
                   module_width, phase_l1, phase_l2, phase_l3, start_phase,
                   linked_rcd_device_id, name
            FROM electrical_cabinet_components
            WHERE deleted_at IS NULL AND component_type='phase_rail'
        """)).mappings()
    ]
    devices = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT device.id, device.distribution_id, device.area_id,
                   device.row_number, device.start_position, device.module_width,
                   device.poles, device.device_type
            FROM electrical_protective_devices AS device
            JOIN electrical_components AS component ON component.id=device.id
            WHERE component.deleted_at IS NULL
              AND device.row_number IS NOT NULL
              AND device.start_position IS NOT NULL
              AND device.module_width IS NOT NULL
        """)).mappings()
    ]

    desired: dict[tuple[str, str], set[str]] = {}
    for device in devices:
        device_start = int(device["start_position"])
        device_end = device_start + int(device["module_width"]) - 1
        candidates = []
        for rail in rails:
            rail_start = int(rail["start_position"])
            rail_end = rail_start + int(rail["module_width"]) - 1
            if (
                _key(device["distribution_id"]) == _key(rail["distribution_id"])
                and _key(device["area_id"]) == _key(rail["area_id"])
                and int(device["row_number"]) == int(rail["row_number"])
                and _key(device["id"]) != _key(rail["linked_rcd_device_id"])
                and rail_start <= device_start
                and device_end <= rail_end
            ):
                candidates.append(rail)
        candidates.sort(
            key=lambda rail: (
                int(rail["module_width"]),
                int(rail["start_position"]),
                str(rail["name"]).casefold(),
                _key(rail["id"]) or "",
            )
        )
        if not candidates:
            continue
        rail = candidates[0]
        pattern = _pattern(rail)
        if not pattern:
            continue
        offset = device_start - int(rail["start_position"])
        count = _active_line_count(device["device_type"], device["poles"])
        phases = {
            pattern[(offset + index) % len(pattern)] for index in range(count)
        }
        desired[(_key(rail["id"]) or "", _key(device["id"]) or "")] = phases

    existing_rows = list(connection.execute(sa.text("""
        SELECT link.id, link.source_kind, link.source_id, link.target_kind,
               link.target_id, link.deleted_at,
               component.component_type AS source_component_type
        FROM electrical_connections AS link
        LEFT JOIN electrical_cabinet_components AS component
          ON component.id=link.source_id AND link.source_kind='cabinet_component'
        WHERE (
            link.source_kind='cabinet_component'
            AND link.target_kind='protective_device'
            AND component.component_type='phase_rail'
        ) OR (
            link.source_kind='protective_device'
            AND link.target_kind='cabinet_component'
            AND EXISTS (
                SELECT 1 FROM electrical_cabinet_components AS target_component
                WHERE target_component.id=link.target_id
                  AND target_component.component_type='phase_rail'
            )
        )
    """)).mappings())
    by_pair: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in existing_rows:
        if row["source_kind"] == "cabinet_component":
            pair = (_key(row["source_id"]) or "", _key(row["target_id"]) or "")
            by_pair.setdefault(pair, []).append(dict(row))
        else:
            reverse_pair = (
                _key(row["target_id"]) or "",
                _key(row["source_id"]) or "",
            )
            # Preserve legitimate upstream protective-device -> phase-rail
            # supplies. Only a reversed record for an actual downstream contact
            # is stale and can be repaired automatically.
            if reverse_pair in desired:
                _archive_connection(connection, row["id"], now)

    for pair, phases in desired.items():
        rows = by_pair.get(pair, [])
        rows.sort(key=lambda row: (row["deleted_at"] is not None, str(row["id"])))
        row = rows[0] if rows else None
        values = {
            "rail_id": pair[0],
            "device_id": pair[1],
            "l1": "L1" in phases,
            "l2": "L2" in phases,
            "l3": "L3" in phases,
            "now": now,
        }
        if row is None:
            authoritative_id = uuid4().hex
            connection.execute(sa.text("""
                INSERT INTO electrical_connections (
                    id, source_kind, source_id, target_kind, target_id,
                    connection_type, label, phase_l1, phase_l2, phase_l3,
                    neutral, protective_earth, cable_type, cores,
                    cross_section_mm2, length_m, route, notes,
                    created_at, updated_at, deleted_at
                ) VALUES (
                    :id, 'cabinet_component', :rail_id,
                    'protective_device', :device_id, 'busbar', NULL,
                    :l1, :l2, :l3, 0, 0, NULL, NULL, NULL, NULL,
                    NULL, NULL, :now, :now, NULL
                )
            """), {**values, "id": authoritative_id})
        else:
            authoritative_id = str(row["id"])
            connection.execute(sa.text("""
                UPDATE electrical_connections
                SET connection_type='busbar', label=NULL,
                    phase_l1=:l1, phase_l2=:l2, phase_l3=:l3,
                    neutral=0, protective_earth=0,
                    cable_type=NULL, cores=NULL, cross_section_mm2=NULL,
                    length_m=NULL, route=NULL, notes=NULL,
                    deleted_at=NULL, updated_at=:now
                WHERE id=:id
            """), {**values, "id": row["id"]})
            for duplicate in rows[1:]:
                connection.execute(sa.text("""
                    UPDATE smart_meter_measurement_points
                    SET connection_id=:authoritative_id, updated_at=:now
                    WHERE connection_id=:duplicate_id AND deleted_at IS NULL
                """), {
                    "authoritative_id": authoritative_id,
                    "duplicate_id": duplicate["id"],
                    "now": now,
                })
                _archive_connection(
                    connection,
                    duplicate["id"],
                    now,
                    replacement_id=authoritative_id,
                )

        downstream_ids = [
            item["id"]
            for item in connection.execute(sa.text("""
                SELECT link.id
                FROM electrical_connections AS link
                LEFT JOIN electrical_cabinet_components AS target_component
                  ON target_component.id=link.target_id
                 AND link.target_kind='cabinet_component'
                WHERE link.source_kind='protective_device'
                  AND link.source_id=:device_id
                  AND link.deleted_at IS NULL
                  AND link.target_kind!='protective_device'
                  AND NOT (
                    link.target_kind='cabinet_component'
                    AND target_component.component_type='phase_rail'
                  )
            """), {"device_id": pair[1]}).mappings()
        ]
        for downstream_id in downstream_ids:
            connection.execute(sa.text("""
                UPDATE electrical_connections
                SET phase_l1=:l1, phase_l2=:l2, phase_l3=:l3, updated_at=:now
                WHERE id=:connection_id
            """), {
                "l1": "L1" in phases,
                "l2": "L2" in phases,
                "l3": "L3" in phases,
                "now": now,
                "connection_id": downstream_id,
            })
            if len(phases) == 1:
                connection.execute(sa.text("""
                    UPDATE smart_meter_measurement_points
                    SET phase=:phase, updated_at=:now
                    WHERE connection_id=:connection_id AND deleted_at IS NULL
                      AND (phase IS NULL OR phase IN ('L1', 'L2', 'L3'))
                """), {
                    "phase": next(iter(phases)),
                    "now": now,
                    "connection_id": downstream_id,
                })

        obsolete_ids = [
            item["id"]
            for item in connection.execute(sa.text("""
                SELECT id FROM electrical_connections
                WHERE target_kind='protective_device' AND target_id=:device_id
                  AND id<>:authoritative_id AND deleted_at IS NULL
            """), {
                "device_id": pair[1],
                "authoritative_id": authoritative_id,
            }).mappings()
        ]
        for obsolete_id in obsolete_ids:
            _archive_connection(
                connection,
                obsolete_id,
                now,
                replacement_id=authoritative_id,
            )

        if len(phases) == 1:
            effective_phase = next(iter(phases))
            connection.execute(sa.text("""
                UPDATE smart_meter_measurement_points
                SET phase=:phase, updated_at=:now
                WHERE connection_id=:connection_id AND deleted_at IS NULL
                  AND (phase IS NULL OR phase IN ('L1', 'L2', 'L3'))
            """), {
                "phase": effective_phase,
                "now": now,
                "connection_id": authoritative_id,
            })

    for pair, rows in by_pair.items():
        if pair in desired:
            continue
        for row in rows:
            _archive_connection(connection, row["id"], now)

    # A measurement channel attached to a genuinely single-phase connection must
    # follow that conductor. This repairs historic points outside the phase-rail
    # paths as well, without guessing on multi-phase connections.
    connection.execute(sa.text("""
        UPDATE smart_meter_measurement_points
        SET phase=(
            SELECT CASE
                WHEN link.phase_l1=1 AND link.phase_l2=0 AND link.phase_l3=0 THEN 'L1'
                WHEN link.phase_l1=0 AND link.phase_l2=1 AND link.phase_l3=0 THEN 'L2'
                WHEN link.phase_l1=0 AND link.phase_l2=0 AND link.phase_l3=1 THEN 'L3'
            END
            FROM electrical_connections AS link
            WHERE link.id=smart_meter_measurement_points.connection_id
              AND link.deleted_at IS NULL
        ), updated_at=:now
        WHERE deleted_at IS NULL
          AND EXISTS (
            SELECT 1 FROM electrical_connections AS link
            WHERE link.id=smart_meter_measurement_points.connection_id
              AND link.deleted_at IS NULL
              AND (CAST(link.phase_l1 AS INTEGER)
                   + CAST(link.phase_l2 AS INTEGER)
                   + CAST(link.phase_l3 AS INTEGER))=1
          )
          AND (phase IS NULL OR phase IN ('L1', 'L2', 'L3'))
    """), {"now": now})


def _repair_circuit_outputs(connection: sa.Connection) -> None:
    """Propagate an unambiguous circuit input phase to all circuit outputs."""
    now = datetime.now(UTC)
    incoming: dict[str, set[tuple[str, ...]]] = {}
    for row in connection.execute(sa.text("""
        SELECT target_id, phase_l1, phase_l2, phase_l3
        FROM electrical_connections
        WHERE target_kind='circuit' AND deleted_at IS NULL
    """)).mappings():
        phases = tuple(
            phase
            for phase, column in (("L1", "phase_l1"), ("L2", "phase_l2"), ("L3", "phase_l3"))
            if bool(row[column])
        )
        if phases:
            incoming.setdefault(_key(row["target_id"]) or "", set()).add(phases)

    for circuit_id, phase_sets in incoming.items():
        if len(phase_sets) != 1:
            continue
        phases = next(iter(phase_sets))
        values = {
            "circuit_id": circuit_id,
            "l1": "L1" in phases,
            "l2": "L2" in phases,
            "l3": "L3" in phases,
            "now": now,
        }
        connection.execute(sa.text("""
            UPDATE electrical_connections
            SET phase_l1=:l1, phase_l2=:l2, phase_l3=:l3, updated_at=:now
            WHERE source_kind='circuit' AND source_id=:circuit_id
              AND deleted_at IS NULL
        """), values)
        if len(phases) == 1:
            connection.execute(sa.text("""
                UPDATE smart_meter_measurement_points
                SET phase=:phase, updated_at=:now
                WHERE deleted_at IS NULL
                  AND connection_id IN (
                    SELECT id FROM electrical_connections
                    WHERE source_kind='circuit' AND source_id=:circuit_id
                      AND deleted_at IS NULL
                  )
                  AND (phase IS NULL OR phase IN ('L1', 'L2', 'L3'))
            """), {
                "phase": phases[0],
                "now": now,
                "circuit_id": circuit_id,
            })


def upgrade() -> None:
    connection = op.get_bind()
    _normalize_components(connection)
    _repair_derived_connections(connection)
    _repair_circuit_outputs(connection)
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_phase_rail_conductors",
            "component_type != 'phase_rail' OR "
            "(neutral = 0 AND protective_earth = 0 AND "
            "(phase_l1 = 1 OR phase_l2 = 1 OR phase_l3 = 1) AND "
            "start_phase IS NOT NULL AND mounting_side IS NOT NULL)",
        )
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_neutral_rail_conductors",
            "component_type != 'neutral_rail' OR "
            "(phase_l1 = 0 AND phase_l2 = 0 AND phase_l3 = 0 "
            "AND neutral = 1 AND protective_earth = 0)",
        )
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_pe_rail_conductors",
            "component_type != 'protective_earth_rail' OR "
            "(phase_l1 = 0 AND phase_l2 = 0 AND phase_l3 = 0 "
            "AND neutral = 0 AND protective_earth = 1)",
        )
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_phase_metadata",
            "component_type = 'phase_rail' OR "
            "(start_phase IS NULL AND mounting_side IS NULL)",
        )
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_rcd_link_type",
            "linked_rcd_device_id IS NULL OR "
            "component_type IN ('phase_rail', 'neutral_rail')",
        )


def downgrade() -> None:
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.drop_constraint(
            "ck_electrical_cabinet_components_rcd_link_type", type_="check"
        )
        batch.drop_constraint(
            "ck_electrical_cabinet_components_phase_metadata", type_="check"
        )
        batch.drop_constraint(
            "ck_electrical_cabinet_components_pe_rail_conductors", type_="check"
        )
        batch.drop_constraint(
            "ck_electrical_cabinet_components_neutral_rail_conductors", type_="check"
        )
        batch.drop_constraint(
            "ck_electrical_cabinet_components_phase_rail_conductors", type_="check"
        )
