"""Repair phase-rail connection phases after 0040.

Revision ID: 0041
Revises: 0040
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: str | None = "0040"
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

    required_by_device: dict[str, tuple[str, ...]] = {}
    for device in devices:
        candidates = []
        for rail in rails:
            if _key(rail["distribution_id"]) != _key(device["distribution_id"]):
                continue
            if _key(rail["area_id"]) != _key(device["area_id"]):
                continue
            if int(rail["row_number"]) != int(device["row_number"]):
                continue
            start = int(rail["start_position"])
            end = start + int(rail["module_width"]) - 1
            if start <= int(device["start_position"]) <= end:
                candidates.append(rail)
        candidates.sort(
            key=lambda item: (
                int(item["module_width"]),
                int(item["start_position"]),
                _key(item["id"]) or "",
            )
        )
        if not candidates:
            continue
        rail = candidates[0]
        pattern = _pattern(rail)
        if not pattern:
            continue
        offset = int(device["start_position"]) - int(rail["start_position"])
        count = min(3, int(device.get("poles") or 1))
        phases = tuple(
            dict.fromkeys(
                pattern[(offset + index) % len(pattern)] for index in range(count)
            )
        )
        required_by_device[_key(device["id"]) or ""] = phases

    records = connection.execute(sa.text("""
        SELECT id, source_kind, source_id, target_kind, target_id
        FROM electrical_connections
        WHERE deleted_at IS NULL
          AND (source_kind='protective_device' OR target_kind='protective_device')
    """)).mappings()
    for record in records:
        requirements: list[tuple[str, ...]] = []
        if record["source_kind"] == "protective_device":
            required = required_by_device.get(_key(record["source_id"]) or "")
            if required:
                requirements.append(required)
        if record["target_kind"] == "protective_device":
            required = required_by_device.get(_key(record["target_id"]) or "")
            if required:
                requirements.append(required)
        if not requirements or any(item != requirements[0] for item in requirements[1:]):
            continue
        required = set(requirements[0])
        connection.execute(
            sa.text("""
                UPDATE electrical_connections
                SET phase_l1=:l1, phase_l2=:l2, phase_l3=:l3
                WHERE id=:id
            """),
            {
                "id": record["id"],
                "l1": "L1" in required,
                "l2": "L2" in required,
                "l3": "L3" in required,
            },
        )


def downgrade() -> None:
    # Corrected phase assignments must not be changed back to contradictory values.
    pass
