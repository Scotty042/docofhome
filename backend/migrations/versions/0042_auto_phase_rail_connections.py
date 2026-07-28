"""Create derived phase-rail connections and keep FI assignment optional.

Revision ID: 0042
Revises: 0041
Create Date: 2026-07-27
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0042"
down_revision: str | None = "0041"
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
    if start not in LINE_PHASES or start not in enabled:
        start = enabled[0]
    index = LINE_PHASES.index(start)
    rotated = LINE_PHASES[index:] + LINE_PHASES[:index]
    return [phase for phase in rotated if phase in enabled]


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(UTC)
    rails = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT id, distribution_id, area_id, row_number, start_position,
                   module_width, phase_l1, phase_l2, phase_l3, start_phase
            FROM electrical_cabinet_components
            WHERE deleted_at IS NULL AND component_type='phase_rail'
        """)).mappings()
    ]
    devices = [
        dict(row)
        for row in connection.execute(sa.text("""
            SELECT device.id, device.distribution_id, device.area_id,
                   device.row_number, device.start_position, device.poles
            FROM electrical_protective_devices AS device
            JOIN electrical_components AS component ON component.id=device.id
            WHERE component.deleted_at IS NULL
              AND device.row_number IS NOT NULL
              AND device.start_position IS NOT NULL
        """)).mappings()
    ]

    active_pairs: set[tuple[str, str]] = set()
    for rail in rails:
        pattern = _pattern(rail)
        if not pattern:
            continue
        rail_start = int(rail["start_position"])
        rail_end = rail_start + int(rail["module_width"]) - 1
        covered = [
            device
            for device in devices
            if _key(device["distribution_id"]) == _key(rail["distribution_id"])
            and _key(device["area_id"]) == _key(rail["area_id"])
            and int(device["row_number"]) == int(rail["row_number"])
            and rail_start <= int(device["start_position"]) <= rail_end
        ]
        for device in covered:
            offset = int(device["start_position"]) - rail_start
            count = min(3, int(device.get("poles") or 1))
            phases = set(
                dict.fromkeys(
                    pattern[(offset + index) % len(pattern)] for index in range(count)
                )
            )
            pair = (_key(rail["id"]) or "", _key(device["id"]) or "")
            active_pairs.add(pair)
            existing = connection.execute(
                sa.text("""
                    SELECT id
                    FROM electrical_connections
                    WHERE source_kind='cabinet_component' AND source_id=:rail_id
                      AND target_kind='protective_device' AND target_id=:device_id
                      AND deleted_at IS NULL
                    LIMIT 1
                """),
                {"rail_id": rail["id"], "device_id": device["id"]},
            ).mappings().first()
            values = {
                "l1": "L1" in phases,
                "l2": "L2" in phases,
                "l3": "L3" in phases,
                "now": now,
            }
            if existing:
                connection.execute(
                    sa.text("""
                        UPDATE electrical_connections
                        SET connection_type='busbar', phase_l1=:l1, phase_l2=:l2,
                            phase_l3=:l3, neutral=0, protective_earth=0,
                            updated_at=:now
                        WHERE id=:id
                    """),
                    {**values, "id": existing["id"]},
                )
            else:
                connection.execute(
                    sa.text("""
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
                    """),
                    {
                        **values,
                        "id": uuid4().hex,
                        "rail_id": rail["id"],
                        "device_id": device["id"],
                    },
                )

    # Remove obsolete direct busbar links from active phase rails and reverse
    # links that contradict the physical supply direction.
    records = connection.execute(sa.text("""
        SELECT link.id, link.source_kind, link.source_id, link.target_kind, link.target_id
        FROM electrical_connections AS link
        LEFT JOIN electrical_cabinet_components AS component
          ON component.id = CASE
            WHEN link.source_kind='cabinet_component' THEN link.source_id
            ELSE link.target_id
          END
        WHERE link.deleted_at IS NULL
          AND link.connection_type='busbar'
          AND (
            (link.source_kind='cabinet_component' AND link.target_kind='protective_device')
            OR
            (link.source_kind='protective_device' AND link.target_kind='cabinet_component')
          )
          AND component.component_type='phase_rail'
    """)).mappings()
    for record in records:
        if record["source_kind"] == "cabinet_component":
            pair = (_key(record["source_id"]) or "", _key(record["target_id"]) or "")
            keep = pair in active_pairs
        else:
            keep = False
        if not keep:
            connection.execute(
                sa.text("""
                    UPDATE electrical_connections
                    SET deleted_at=:now, updated_at=:now
                    WHERE id=:id
                """),
                {"id": record["id"], "now": now},
            )


def downgrade() -> None:
    # These connections document physical contacts and should not be removed
    # automatically on downgrade.
    pass
