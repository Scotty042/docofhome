"""Add photovoltaic energy balance and multiple supply sources.

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-23
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_index(table_name: str, index_name: str) -> bool:
    return any(
        item["name"] == index_name
        for item in sa.inspect(op.get_bind()).get_indexes(table_name)
    )


def upgrade() -> None:
    with op.batch_alter_table("consumption_meters") as batch:
        batch.drop_constraint("ck_consumption_meters_type", type_="check")
        batch.create_check_constraint(
            "ck_consumption_meters_type",
            "meter_type IN ('water', 'electricity_grid', 'electricity_pv', "
            "'electricity_feed_in', 'gas', 'heat', 'oil', 'other')",
        )

    if _has_index(
        "electrical_connections", "uq_electrical_connections_active_target"
    ):
        op.drop_index(
            "uq_electrical_connections_active_target",
            table_name="electrical_connections",
        )

    op.create_table(
        "energy_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grid_connection_name", sa.String(length=200), nullable=True),
        sa.Column("grid_operator", sa.String(length=200), nullable=True),
        sa.Column("energy_supplier", sa.String(length=200), nullable=True),
        sa.Column("metering_point_id", sa.String(length=200), nullable=True),
        sa.Column("connection_capacity_kw", sa.Float(), nullable=True),
        sa.Column("grid_import_meter_id", sa.Uuid(), nullable=True),
        sa.Column("pv_generation_meter_id", sa.Uuid(), nullable=True),
        sa.Column("grid_export_meter_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "connection_capacity_kw IS NULL OR "
            "(connection_capacity_kw > 0 AND connection_capacity_kw <= 100000)",
            name="ck_energy_configurations_capacity",
        ),
        sa.ForeignKeyConstraint(
            ["grid_import_meter_id"], ["consumption_meters.id"]
        ),
        sa.ForeignKeyConstraint(
            ["pv_generation_meter_id"], ["consumption_meters.id"]
        ),
        sa.ForeignKeyConstraint(
            ["grid_export_meter_id"], ["consumption_meters.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "grid_import_meter_id",
        "pv_generation_meter_id",
        "grid_export_meter_id",
    ):
        op.create_index(
            f"ix_energy_configurations_{column}",
            "energy_configurations",
            [column],
        )
    now = datetime.now(UTC).replace(tzinfo=None)
    op.bulk_insert(
        sa.table(
            "energy_configurations",
            sa.column("id", sa.Integer()),
            sa.column("created_at", sa.DateTime()),
            sa.column("updated_at", sa.DateTime()),
        ),
        [{"id": 1, "created_at": now, "updated_at": now}],
    )

    op.create_table(
        "energy_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("component_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("manufacturer", sa.String(length=200), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("rated_power_kw", sa.Float(), nullable=True),
        sa.Column("capacity_kwh", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "component_type IN ('pv_source', 'inverter', 'storage')",
            name="ck_energy_components_type",
        ),
        sa.CheckConstraint("sort_order >= 0", name="ck_energy_components_sort_order"),
        sa.CheckConstraint(
            "rated_power_kw IS NULL OR (rated_power_kw > 0 AND rated_power_kw <= 100000)",
            name="ck_energy_components_rated_power",
        ),
        sa.CheckConstraint(
            "capacity_kwh IS NULL OR (capacity_kwh > 0 AND capacity_kwh <= 1000000)",
            name="ck_energy_components_capacity",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "component_type",
        "name",
        "asset_id",
        "sort_order",
        "deleted_at",
    ):
        op.create_index(
            f"ix_energy_components_{column}", "energy_components", [column]
        )
    op.create_index(
        "uq_energy_components_active_name_type",
        "energy_components",
        ["component_type", "name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_energy_components_active_name_type", table_name="energy_components"
    )
    for column in (
        "deleted_at",
        "sort_order",
        "asset_id",
        "name",
        "component_type",
    ):
        op.drop_index(f"ix_energy_components_{column}", table_name="energy_components")
    op.drop_table("energy_components")

    for column in (
        "grid_export_meter_id",
        "pv_generation_meter_id",
        "grid_import_meter_id",
    ):
        op.drop_index(
            f"ix_energy_configurations_{column}", table_name="energy_configurations"
        )
    op.drop_table("energy_configurations")

    op.create_index(
        "uq_electrical_connections_active_target",
        "electrical_connections",
        ["target_kind", "target_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    with op.batch_alter_table("consumption_meters") as batch:
        batch.drop_constraint("ck_consumption_meters_type", type_="check")
        batch.create_check_constraint(
            "ck_consumption_meters_type",
            "meter_type IN ('water', 'electricity_grid', 'electricity_pv', "
            "'gas', 'heat', 'oil', 'other')",
        )
