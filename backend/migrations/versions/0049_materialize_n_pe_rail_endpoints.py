"""Materialize N and PE layout areas as electrical topology endpoints.

Revision ID: 0049
Revises: 0048
Create Date: 2026-07-28
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0049"
down_revision: str | None = "0048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DESCRIPTION = "Automatisch aus dem Schienenbereich erzeugter elektrischer Endpunkt."


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    required_tables = {
        "electrical_distribution_areas",
        "electrical_distribution_sections",
        "electrical_cabinet_components",
    }
    if not required_tables.issubset(set(inspector.get_table_names())):
        return

    areas = bind.execute(
        sa.text(
            """
            SELECT area.id, area.name, area.area_type, section.distribution_id
            FROM electrical_distribution_areas AS area
            JOIN electrical_distribution_sections AS section
              ON section.id = area.section_id
            WHERE area.deleted_at IS NULL
              AND section.deleted_at IS NULL
              AND area.area_type IN ('neutral_rail', 'protective_earth_rail')
            """
        )
    ).mappings().all()
    now = datetime.now(UTC)
    for area in areas:
        existing = bind.execute(
            sa.text(
                """
                SELECT id
                FROM electrical_cabinet_components
                WHERE area_id = :area_id
                  AND component_type = :component_type
                  AND deleted_at IS NULL
                LIMIT 1
                """
            ),
            {
                "area_id": area["id"],
                "component_type": area["area_type"],
            },
        ).first()
        if existing is not None:
            continue
        is_neutral = area["area_type"] == "neutral_rail"
        bind.execute(
            sa.text(
                """
                INSERT INTO electrical_cabinet_components (
                    id, distribution_id, area_id, component_type, name,
                    row_number, start_position, module_width,
                    phase_l1, phase_l2, phase_l3, neutral, protective_earth,
                    rated_current_a, max_cross_section_mm2, outgoing_connections,
                    linked_rcd_device_id, linked_rcd_asset_id,
                    start_phase, mounting_side, description, notes,
                    created_at, updated_at, deleted_at
                ) VALUES (
                    :id, :distribution_id, :area_id, :component_type, :name,
                    1, 1, 1,
                    0, 0, 0, :neutral, :protective_earth,
                    NULL, NULL, NULL,
                    NULL, NULL,
                    NULL, NULL, :description, NULL,
                    :created_at, :updated_at, NULL
                )
                """
            ),
            {
                "id": uuid4().hex,
                "distribution_id": area["distribution_id"],
                "area_id": area["id"],
                "component_type": area["area_type"],
                "name": area["name"],
                "neutral": 1 if is_neutral else 0,
                "protective_earth": 0 if is_neutral else 1,
                "description": _DESCRIPTION,
                "created_at": now,
                "updated_at": now,
            },
        )


def downgrade() -> None:
    # Deliberately keep the materialized rail components. They are valid cabinet
    # components in 1.7.1 as well, and deleting them could orphan wiring created
    # after the upgrade.
    pass
