"""Add passive cabinet components and rows-layout placements.

Revision ID: 0031
Revises: 0030
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("electrical_asset_placements") as batch:
        batch.alter_column(
            "area_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )

    op.create_table(
        "electrical_cabinet_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("area_id", sa.Uuid(), nullable=True),
        sa.Column("component_type", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("start_position", sa.Integer(), nullable=False),
        sa.Column("module_width", sa.Integer(), nullable=False),
        sa.Column("phase_l1", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("phase_l2", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("phase_l3", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("neutral", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "protective_earth", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("rated_current_a", sa.Float(), nullable=True),
        sa.Column("max_cross_section_mm2", sa.Float(), nullable=True),
        sa.Column("outgoing_connections", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "component_type IN ('phase_distribution_block', 'busbar', 'phase_rail', "
            "'neutral_rail', 'protective_earth_rail', 'terminal_block', "
            "'connection_block', 'potential_distribution', 'other')",
            name="ck_electrical_cabinet_components_type",
        ),
        sa.CheckConstraint(
            "row_number >= 1 AND row_number <= 100",
            name="ck_electrical_cabinet_components_row",
        ),
        sa.CheckConstraint(
            "start_position >= 1 AND start_position <= 1000",
            name="ck_electrical_cabinet_components_start",
        ),
        sa.CheckConstraint(
            "module_width >= 1 AND module_width <= 100",
            name="ck_electrical_cabinet_components_width",
        ),
        sa.CheckConstraint(
            "rated_current_a IS NULL OR (rated_current_a > 0 AND rated_current_a <= 10000)",
            name="ck_electrical_cabinet_components_current",
        ),
        sa.CheckConstraint(
            "max_cross_section_mm2 IS NULL OR "
            "(max_cross_section_mm2 > 0 AND max_cross_section_mm2 <= 1000)",
            name="ck_electrical_cabinet_components_cross_section",
        ),
        sa.CheckConstraint(
            "outgoing_connections IS NULL OR "
            "(outgoing_connections >= 1 AND outgoing_connections <= 1000)",
            name="ck_electrical_cabinet_components_outputs",
        ),
        sa.ForeignKeyConstraint(
            ["distribution_id"], ["electrical_distributions.id"]
        ),
        sa.ForeignKeyConstraint(["area_id"], ["electrical_distribution_areas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "distribution_id",
        "area_id",
        "component_type",
        "row_number",
        "start_position",
        "deleted_at",
    ):
        op.create_index(
            f"ix_electrical_cabinet_components_{column}",
            "electrical_cabinet_components",
            [column],
        )
    op.create_index(
        "ix_electrical_cabinet_components_area_row",
        "electrical_cabinet_components",
        ["area_id", "row_number", "start_position"],
    )
    op.create_index(
        "ix_electrical_cabinet_components_distribution_row",
        "electrical_cabinet_components",
        ["distribution_id", "row_number", "start_position"],
    )

    with op.batch_alter_table("electrical_connections") as batch:
        batch.drop_constraint("ck_electrical_connections_source_kind", type_="check")
        batch.drop_constraint("ck_electrical_connections_target_kind", type_="check")
        batch.create_check_constraint(
            "ck_electrical_connections_source_kind",
            "source_kind IN ('grid_connection', 'asset', 'distribution', "
            "'protective_device', 'cabinet_component', 'circuit')",
        )
        batch.create_check_constraint(
            "ck_electrical_connections_target_kind",
            "target_kind IN ('asset', 'distribution', 'protective_device', "
            "'cabinet_component', 'circuit')",
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM electrical_connections "
            "WHERE source_kind = 'cabinet_component' "
            "OR target_kind = 'cabinet_component'"
        )
    )
    with op.batch_alter_table("electrical_connections") as batch:
        batch.drop_constraint("ck_electrical_connections_source_kind", type_="check")
        batch.drop_constraint("ck_electrical_connections_target_kind", type_="check")
        batch.create_check_constraint(
            "ck_electrical_connections_source_kind",
            "source_kind IN ('grid_connection', 'asset', 'distribution', "
            "'protective_device', 'circuit')",
        )
        batch.create_check_constraint(
            "ck_electrical_connections_target_kind",
            "target_kind IN ('asset', 'distribution', 'protective_device', 'circuit')",
        )

    op.drop_index(
        "ix_electrical_cabinet_components_distribution_row",
        table_name="electrical_cabinet_components",
    )
    op.drop_index(
        "ix_electrical_cabinet_components_area_row",
        table_name="electrical_cabinet_components",
    )
    for column in reversed(
        (
            "distribution_id",
            "area_id",
            "component_type",
            "row_number",
            "start_position",
            "deleted_at",
        )
    ):
        op.drop_index(
            f"ix_electrical_cabinet_components_{column}",
            table_name="electrical_cabinet_components",
        )
    op.drop_table("electrical_cabinet_components")

    # Rows-layout DIN asset placements cannot be represented by revision 0030.
    op.execute(
        sa.text("DELETE FROM electrical_asset_placements WHERE area_id IS NULL")
    )
    with op.batch_alter_table("electrical_asset_placements") as batch:
        batch.alter_column(
            "area_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
