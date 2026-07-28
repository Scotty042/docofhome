"""Connect phase rails to all physically covered DIN devices.

Revision ID: 0045
Revises: 0044
Create Date: 2026-07-28
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: str | None = "0044"
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


def _protective_line_count(device_type: object, poles: object) -> int:
    count = max(1, int(poles or 1))
    # 2P and 4P FI/FI-LS/SPD include one neutral pole. On a three-phase comb
    # rail only the line poles are contacted; the fourth pole remains free for N.
    if str(device_type) in {"rcd", "rcbo", "spd"} and count in {2, 4}:
        count -= 1
    return min(3, count)


def _archive_connection(
    connection: sa.Connection,
    connection_id: object,
    now: datetime,
    *,
    replacement_id: object | None = None,
) -> None:
    if replacement_id is not None:
        connection.execute(sa.text("""
            UPDATE smart_meter_measurement_points
            SET connection_id=:replacement_id, updated_at=:now
            WHERE connection_id=:connection_id AND deleted_at IS NULL
        """), {
            "replacement_id": replacement_id,
            "connection_id": connection_id,
            "now": now,
        })
    else:
        point_ids = [
            row["id"]
            for row in connection.execute(sa.text("""
                SELECT id FROM smart_meter_measurement_points
                WHERE connection_id=:connection_id AND deleted_at IS NULL
            """), {"connection_id": connection_id}).mappings()
        ]
        for point_id in point_ids:
            connection.execute(sa.text("""
                DELETE FROM smart_meter_measurement_entities
                WHERE measurement_point_id=:point_id
            """), {"point_id": point_id})
        connection.execute(sa.text("""
            UPDATE smart_meter_measurement_points
            SET deleted_at=:now, updated_at=:now
            WHERE connection_id=:connection_id AND deleted_at IS NULL
        """), {"connection_id": connection_id, "now": now})
    connection.execute(sa.text("""
        UPDATE electrical_connections
        SET deleted_at=:now, updated_at=:now
        WHERE id=:connection_id AND deleted_at IS NULL
    """), {"connection_id": connection_id, "now": now})


def _desired_contacts(connection: sa.Connection) -> dict[tuple[str, str, str], set[str]]:
    rails = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT id, distribution_id, area_id, row_number, start_position,
                   module_width, phase_l1, phase_l2, phase_l3, start_phase, name
            FROM electrical_cabinet_components
            WHERE deleted_at IS NULL AND component_type='phase_rail'
        """)).mappings()
    ]

    protective_rows = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT device.id, component.asset_id, device.distribution_id,
                   device.area_id, device.row_number, device.start_position,
                   COALESCE(
                       device.module_width,
                       asset.module_width,
                       CASE WHEN product.din_rail_mount=1 THEN product.module_width END,
                       asset_type.module_width
                   ) AS effective_width,
                   device.poles, device.device_type,
                   asset.name
            FROM electrical_protective_devices AS device
            JOIN electrical_components AS component ON component.id=device.id
            JOIN assets AS asset ON asset.id=component.asset_id
            LEFT JOIN products AS product ON product.id=asset.product_id
            LEFT JOIN asset_types AS asset_type ON asset_type.id=asset.asset_type_id
            WHERE component.deleted_at IS NULL
              AND asset.deleted_at IS NULL
              AND asset.status!='retired'
              AND device.row_number IS NOT NULL
              AND device.start_position IS NOT NULL
        """)).mappings()
    ]
    asset_rows = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT placement.asset_id AS id, placement.distribution_id,
                   placement.area_id, placement.row_number,
                   placement.start_position, placement.module_width AS effective_width,
                   asset.name
            FROM electrical_asset_placements AS placement
            JOIN assets AS asset ON asset.id=placement.asset_id
            LEFT JOIN electrical_components AS component
              ON component.asset_id=placement.asset_id
             AND component.deleted_at IS NULL
            WHERE placement.deleted_at IS NULL
              AND asset.deleted_at IS NULL
              AND asset.status!='retired'
              AND component.id IS NULL
        """)).mappings()
    ]

    targets: list[dict[str, object]] = []
    for row in protective_rows:
        if row["effective_width"] is None:
            continue
        row["target_kind"] = "protective_device"
        row["target_id"] = row["id"]
        row["phase_count"] = _protective_line_count(row["device_type"], row["poles"])
        targets.append(row)
    for row in asset_rows:
        row["target_kind"] = "asset"
        row["target_id"] = row["id"]
        row["phase_count"] = int(row["effective_width"])
        targets.append(row)

    desired: dict[tuple[str, str, str], set[str]] = {}
    for target in targets:
        target_start = int(target["start_position"])
        target_width = int(target["effective_width"])
        target_end = target_start + target_width - 1
        candidates: list[dict[str, object]] = []
        for rail in rails:
            rail_start = int(rail["start_position"])
            rail_end = rail_start + int(rail["module_width"]) - 1
            if (
                _key(target["distribution_id"]) == _key(rail["distribution_id"])
                and _key(target["area_id"]) == _key(rail["area_id"])
                and int(target["row_number"]) == int(rail["row_number"])
                and rail_start <= target_start
                and target_end <= rail_end
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
        offset = target_start - int(rail["start_position"])
        count = max(1, int(target["phase_count"]))
        phases = {
            pattern[(offset + index) % len(pattern)]
            for index in range(count)
        }
        desired[(
            _key(rail["id"]) or "",
            str(target["target_kind"]),
            _key(target["target_id"]) or "",
        )] = phases
    return desired


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(UTC)
    desired = _desired_contacts(connection)

    existing_rows = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT link.id, link.source_id, link.target_kind, link.target_id,
                   link.deleted_at
            FROM electrical_connections AS link
            JOIN electrical_cabinet_components AS component
              ON component.id=link.source_id
            WHERE link.source_kind='cabinet_component'
              AND link.target_kind IN ('protective_device', 'asset')
              AND link.connection_type='busbar'
              AND component.component_type='phase_rail'
        """)).mappings()
    ]
    by_key: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in existing_rows:
        key = (
            _key(row["source_id"]) or "",
            str(row["target_kind"]),
            _key(row["target_id"]) or "",
        )
        by_key.setdefault(key, []).append(row)

    for key, phases in desired.items():
        rows = by_key.get(key, [])
        rows.sort(key=lambda row: (row["deleted_at"] is not None, str(row["id"])))
        authoritative = rows[0] if rows else None
        values = {
            "rail_id": key[0],
            "target_kind": key[1],
            "target_id": key[2],
            "l1": "L1" in phases,
            "l2": "L2" in phases,
            "l3": "L3" in phases,
            "now": now,
        }
        if authoritative is None:
            authoritative_id = uuid4().hex
            # Insert inactive first for upgraded databases that may still retain
            # a historical single-active-target index.
            connection.execute(sa.text("""
                INSERT INTO electrical_connections (
                    id, source_kind, source_id, target_kind, target_id,
                    connection_type, label, phase_l1, phase_l2, phase_l3,
                    neutral, protective_earth, cable_type, cores,
                    cross_section_mm2, length_m, route, notes,
                    created_at, updated_at, deleted_at
                ) VALUES (
                    :id, 'cabinet_component', :rail_id, :target_kind, :target_id,
                    'busbar', NULL, :l1, :l2, :l3, 0, 0,
                    NULL, NULL, NULL, NULL, NULL, NULL, :now, :now, :now
                )
            """), {**values, "id": authoritative_id})
        else:
            authoritative_id = str(authoritative["id"])
            connection.execute(sa.text("""
                UPDATE electrical_connections
                SET connection_type='busbar', label=NULL,
                    phase_l1=:l1, phase_l2=:l2, phase_l3=:l3,
                    neutral=0, protective_earth=0,
                    cable_type=NULL, cores=NULL, cross_section_mm2=NULL,
                    length_m=NULL, route=NULL, notes=NULL, updated_at=:now
                WHERE id=:id
            """), {**values, "id": authoritative["id"]})

        competing = [
            row["id"]
            for row in connection.execute(sa.text("""
                SELECT id FROM electrical_connections
                WHERE target_kind=:target_kind AND target_id=:target_id
                  AND id!=:authoritative_id AND deleted_at IS NULL
            """), {
                "target_kind": key[1],
                "target_id": key[2],
                "authoritative_id": authoritative_id,
            }).mappings()
        ]
        for competing_id in competing:
            _archive_connection(
                connection,
                competing_id,
                now,
                replacement_id=authoritative_id,
            )
        connection.execute(sa.text("""
            UPDATE electrical_connections
            SET deleted_at=NULL, updated_at=:now
            WHERE id=:id
        """), {"id": authoritative_id, "now": now})

        for duplicate in rows[1:]:
            _archive_connection(
                connection,
                duplicate["id"],
                now,
                replacement_id=authoritative_id,
            )

        # A DIN device fed by the rail carries the same line phases to its
        # downstream topology connections.
        connection.execute(sa.text("""
            UPDATE electrical_connections
            SET phase_l1=:l1, phase_l2=:l2, phase_l3=:l3, updated_at=:now
            WHERE source_kind=:target_kind AND source_id=:target_id
              AND deleted_at IS NULL
              AND NOT (
                  target_kind='cabinet_component'
                  AND EXISTS (
                      SELECT 1 FROM electrical_cabinet_components AS c
                      WHERE c.id=electrical_connections.target_id
                        AND c.component_type='phase_rail'
                  )
              )
        """), values)

    # Archive old derived rail contacts that are no longer physically covered.
    for row in existing_rows:
        key = (
            _key(row["source_id"]) or "",
            str(row["target_kind"]),
            _key(row["target_id"]) or "",
        )
        if key not in desired and row["deleted_at"] is None:
            _archive_connection(connection, row["id"], now)

    # Remove reverse busbar links only when the same DIN target now has the
    # authoritative rail -> target contact. Legitimate unrelated rail feeds stay.
    reverse_rows = connection.execute(sa.text("""
        SELECT id, source_kind, source_id, target_id
        FROM electrical_connections
        WHERE source_kind IN ('protective_device', 'asset')
          AND target_kind='cabinet_component'
          AND connection_type='busbar'
          AND deleted_at IS NULL
    """)).mappings()
    desired_reverse = {(kind, target_id, rail_id) for rail_id, kind, target_id in desired}
    for row in reverse_rows:
        if (
            str(row["source_kind"]),
            _key(row["source_id"]) or "",
            _key(row["target_id"]) or "",
        ) in desired_reverse:
            _archive_connection(connection, row["id"], now)


def downgrade() -> None:
    # The generated links describe physical DIN contacts and remain useful when
    # the application is downgraded. Do not remove them automatically.
    pass
