"""Add collected meter, cabinet, topology and network integration fixes.

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("consumption_meters") as batch:
        batch.add_column(
            sa.Column("home_assistant_power_entity_id", sa.String(length=255), nullable=True)
        )
        batch.add_column(
            sa.Column("home_assistant_voltage_entity_id", sa.String(length=255), nullable=True)
        )
    op.create_index(
        "ix_consumption_meters_home_assistant_power_entity_id",
        "consumption_meters",
        ["home_assistant_power_entity_id"],
    )
    op.create_index(
        "ix_consumption_meters_home_assistant_voltage_entity_id",
        "consumption_meters",
        ["home_assistant_voltage_entity_id"],
    )

    with op.batch_alter_table("electrical_distribution_areas") as batch:
        batch.drop_constraint("ck_electrical_distribution_areas_type", type_="check")
        batch.create_check_constraint(
            "ck_electrical_distribution_areas_type",
            "area_type IN ('device_rows', 'meter', 'connection', 'neutral_rail', "
            "'protective_earth_rail', 'technology', 'reserve', 'cover')",
        )
        batch.add_column(
            sa.Column(
                "width", sa.String(length=10), nullable=False, server_default="full"
            )
        )
        batch.create_check_constraint(
            "ck_electrical_distribution_areas_width",
            "width IN ('full', 'half')",
        )

    op.create_table(
        "electrical_meter_placements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("area_id", sa.Uuid(), nullable=False),
        sa.Column("meter_id", sa.Uuid(), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "position >= 1 AND position <= 100",
            name="ck_electrical_meter_placements_position",
        ),
        sa.CheckConstraint(
            "(meter_id IS NOT NULL AND asset_id IS NULL) OR "
            "(meter_id IS NULL AND asset_id IS NOT NULL)",
            name="ck_electrical_meter_placements_source",
        ),
        sa.ForeignKeyConstraint(["distribution_id"], ["electrical_distributions.id"]),
        sa.ForeignKeyConstraint(["area_id"], ["electrical_distribution_areas.id"]),
        sa.ForeignKeyConstraint(["meter_id"], ["consumption_meters.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("distribution_id", "area_id", "meter_id", "asset_id", "deleted_at"):
        op.create_index(
            f"ix_electrical_meter_placements_{column}",
            "electrical_meter_placements",
            [column],
        )
    op.create_index(
        "uq_electrical_meter_placements_active_meter",
        "electrical_meter_placements",
        ["meter_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_electrical_meter_placements_active_asset",
        "electrical_meter_placements",
        ["asset_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND asset_id IS NOT NULL"),
    )
    op.create_index(
        "uq_electrical_meter_placements_active_area_position",
        "electrical_meter_placements",
        ["area_id", "position"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
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

    with op.batch_alter_table("network_interfaces") as batch:
        batch.add_column(sa.Column("logical_interface_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_network_interfaces_logical_interface",
            "network_interfaces",
            ["logical_interface_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_network_interfaces_logical_interface_distinct",
            "logical_interface_id IS NULL OR logical_interface_id <> id",
        )
    op.create_index(
        "ix_network_interfaces_logical_interface_id",
        "network_interfaces",
        ["logical_interface_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_network_interfaces_logical_interface_id",
        table_name="network_interfaces",
    )
    with op.batch_alter_table("network_interfaces") as batch:
        batch.drop_constraint("ck_network_interfaces_logical_interface_distinct", type_="check")
        batch.drop_constraint("fk_network_interfaces_logical_interface", type_="foreignkey")
        batch.drop_column("logical_interface_id")

    # Connections originating at the new synthetic grid endpoint cannot be
    # represented by revision 0027. Remove them before narrowing the check
    # constraint so a deliberate downgrade remains executable.
    op.execute(
        sa.text(
            "DELETE FROM electrical_connections "
            "WHERE source_kind = 'grid_connection' OR target_kind = 'grid_connection'"
        )
    )

    with op.batch_alter_table("electrical_connections") as batch:
        batch.drop_constraint("ck_electrical_connections_source_kind", type_="check")
        batch.drop_constraint("ck_electrical_connections_target_kind", type_="check")
        batch.create_check_constraint(
            "ck_electrical_connections_source_kind",
            "source_kind IN ('asset', 'distribution', 'protective_device', 'circuit')",
        )
        batch.create_check_constraint(
            "ck_electrical_connections_target_kind",
            "target_kind IN ('asset', 'distribution', 'protective_device', 'circuit')",
        )

    op.drop_index(
        "uq_electrical_meter_placements_active_area_position",
        table_name="electrical_meter_placements",
    )
    op.drop_index(
        "uq_electrical_meter_placements_active_meter",
        table_name="electrical_meter_placements",
    )
    op.drop_index(
        "uq_electrical_meter_placements_active_asset",
        table_name="electrical_meter_placements",
    )
    for column in ("deleted_at", "asset_id", "meter_id", "area_id", "distribution_id"):
        op.drop_index(
            f"ix_electrical_meter_placements_{column}",
            table_name="electrical_meter_placements",
        )
    op.drop_table("electrical_meter_placements")

    # Revision 0027 only knows a generic connection field. Preserve the
    # cabinet layout as closely as possible by converting N/PE rails before
    # restoring the narrower area-type constraint.
    op.execute(
        sa.text(
            "UPDATE electrical_distribution_areas SET area_type = 'connection' "
            "WHERE area_type IN ('neutral_rail', 'protective_earth_rail')"
        )
    )

    with op.batch_alter_table("electrical_distribution_areas") as batch:
        batch.drop_constraint("ck_electrical_distribution_areas_width", type_="check")
        batch.drop_constraint("ck_electrical_distribution_areas_type", type_="check")
        batch.drop_column("width")
        batch.create_check_constraint(
            "ck_electrical_distribution_areas_type",
            "area_type IN ('device_rows', 'meter', 'connection', 'technology', 'reserve', 'cover')",
        )

    op.drop_index(
        "ix_consumption_meters_home_assistant_voltage_entity_id",
        table_name="consumption_meters",
    )
    op.drop_index(
        "ix_consumption_meters_home_assistant_power_entity_id",
        table_name="consumption_meters",
    )
    with op.batch_alter_table("consumption_meters") as batch:
        batch.drop_column("home_assistant_voltage_entity_id")
        batch.drop_column("home_assistant_power_entity_id")
