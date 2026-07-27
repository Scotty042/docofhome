"""Add electrical device defaults and Smart-Meter measurement points.

Revision ID: 0037
Revises: 0036
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_BREAKER_CHECK = (
    "breaker_characteristic IS NULL OR "
    "breaker_characteristic IN ('B', 'C', 'D', 'K', 'Z')"
)
_CURRENT_CHECK = (
    "rated_current_a IS NULL OR (rated_current_a > 0 AND rated_current_a <= 10000)"
)


_COIL_VOLTAGE_CHECK = (
    "coil_voltage_v IS NULL OR (coil_voltage_v > 0 AND coil_voltage_v <= 10000)"
)
_COIL_VOLTAGE_TYPE_CHECK = (
    "coil_voltage_type IS NULL OR coil_voltage_type IN ('AC', 'DC')"
)
_CONTACT_COUNT_CHECK = (
    "contact_count IS NULL OR (contact_count >= 1 AND contact_count <= 100)"
)
_CONTACT_TYPE_CHECK = (
    "contact_type IS NULL OR "
    "contact_type IN ('normally_open', 'normally_closed', 'changeover')"
)


def upgrade() -> None:
    with op.batch_alter_table("asset_types") as batch:
        batch.add_column(sa.Column("breaker_characteristic", sa.String(length=2)))
        batch.add_column(sa.Column("rated_current_a", sa.Float()))
        batch.add_column(sa.Column("coil_voltage_v", sa.Float()))
        batch.add_column(sa.Column("coil_voltage_type", sa.String(length=2)))
        batch.add_column(sa.Column("contact_count", sa.Integer()))
        batch.add_column(sa.Column("contact_type", sa.String(length=30)))
        batch.create_check_constraint(
            "ck_asset_types_breaker_characteristic",
            _BREAKER_CHECK,
        )
        batch.create_check_constraint(
            "ck_asset_types_rated_current",
            _CURRENT_CHECK,
        )
        batch.create_check_constraint(
            "ck_asset_types_coil_voltage",
            _COIL_VOLTAGE_CHECK,
        )
        batch.create_check_constraint(
            "ck_asset_types_coil_voltage_type",
            _COIL_VOLTAGE_TYPE_CHECK,
        )
        batch.create_check_constraint(
            "ck_asset_types_contact_count",
            _CONTACT_COUNT_CHECK,
        )
        batch.create_check_constraint(
            "ck_asset_types_contact_type",
            _CONTACT_TYPE_CHECK,
        )

    with op.batch_alter_table("assets") as batch:
        batch.add_column(sa.Column("breaker_characteristic", sa.String(length=2)))
        batch.add_column(sa.Column("rated_current_a", sa.Float()))
        batch.add_column(sa.Column("coil_voltage_v", sa.Float()))
        batch.add_column(sa.Column("coil_voltage_type", sa.String(length=2)))
        batch.add_column(sa.Column("contact_count", sa.Integer()))
        batch.add_column(sa.Column("contact_type", sa.String(length=30)))
        batch.create_check_constraint(
            "ck_assets_breaker_characteristic",
            _BREAKER_CHECK,
        )
        batch.create_check_constraint(
            "ck_assets_rated_current",
            _CURRENT_CHECK,
        )
        batch.create_check_constraint(
            "ck_assets_coil_voltage",
            _COIL_VOLTAGE_CHECK,
        )
        batch.create_check_constraint(
            "ck_assets_coil_voltage_type",
            _COIL_VOLTAGE_TYPE_CHECK,
        )
        batch.create_check_constraint(
            "ck_assets_contact_count",
            _CONTACT_COUNT_CHECK,
        )
        batch.create_check_constraint(
            "ck_assets_contact_type",
            _CONTACT_TYPE_CHECK,
        )

    op.create_table(
        "smart_meter_measurement_points",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("smart_meter_asset_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("channel_name", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("phase", sa.String(length=2), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False, server_default="unspecified"),
        sa.Column("inverted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("transformer_nominal_current_a", sa.Float(), nullable=True),
        sa.Column("transformer_ratio", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "phase IS NULL OR phase IN ('L1', 'L2', 'L3', 'N')",
            name="ck_smart_meter_measurement_points_phase",
        ),
        sa.CheckConstraint(
            "direction IN ('unspecified', 'source_to_target', 'target_to_source')",
            name="ck_smart_meter_measurement_points_direction",
        ),
        sa.CheckConstraint(
            "transformer_nominal_current_a IS NULL OR "
            "(transformer_nominal_current_a > 0 AND transformer_nominal_current_a <= 100000)",
            name="ck_smart_meter_measurement_points_nominal_current",
        ),
        sa.ForeignKeyConstraint(
            ["smart_meter_asset_id"],
            ["assets.id"],
            name="fk_smart_meter_measurement_points_asset",
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["electrical_connections.id"],
            name="fk_smart_meter_measurement_points_connection",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_smart_meter_measurement_points_asset",
        "smart_meter_measurement_points",
        ["smart_meter_asset_id"],
    )
    op.create_index(
        "ix_smart_meter_measurement_points_connection",
        "smart_meter_measurement_points",
        ["connection_id"],
    )
    op.create_index(
        "ix_smart_meter_measurement_points_deleted_at",
        "smart_meter_measurement_points",
        ["deleted_at"],
    )
    op.create_index(
        "uq_smart_meter_measurement_points_active_channel",
        "smart_meter_measurement_points",
        ["smart_meter_asset_id", "channel_name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "smart_meter_measurement_entities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("measurement_point_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('power', 'current', 'voltage', 'energy', 'energy_import', "
            "'energy_export', 'frequency', 'power_factor', 'additional')",
            name="ck_smart_meter_measurement_entities_role",
        ),
        sa.CheckConstraint(
            "length(trim(entity_id)) BETWEEN 3 AND 255 AND instr(entity_id, '.') > 1",
            name="ck_smart_meter_measurement_entities_entity_id",
        ),
        sa.ForeignKeyConstraint(
            ["measurement_point_id"],
            ["smart_meter_measurement_points.id"],
            name="fk_smart_meter_measurement_entities_point",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "measurement_point_id",
            "entity_id",
            name="uq_smart_meter_measurement_entities_point_entity",
        ),
    )
    op.create_index(
        "ix_smart_meter_measurement_entities_point",
        "smart_meter_measurement_entities",
        ["measurement_point_id"],
    )
    op.create_index(
        "ix_smart_meter_measurement_entities_entity_id",
        "smart_meter_measurement_entities",
        ["entity_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_smart_meter_measurement_entities_entity_id",
        table_name="smart_meter_measurement_entities",
    )
    op.drop_index(
        "ix_smart_meter_measurement_entities_point",
        table_name="smart_meter_measurement_entities",
    )
    op.drop_table("smart_meter_measurement_entities")

    op.drop_index(
        "uq_smart_meter_measurement_points_active_channel",
        table_name="smart_meter_measurement_points",
    )
    op.drop_index(
        "ix_smart_meter_measurement_points_deleted_at",
        table_name="smart_meter_measurement_points",
    )
    op.drop_index(
        "ix_smart_meter_measurement_points_connection",
        table_name="smart_meter_measurement_points",
    )
    op.drop_index(
        "ix_smart_meter_measurement_points_asset",
        table_name="smart_meter_measurement_points",
    )
    op.drop_table("smart_meter_measurement_points")

    with op.batch_alter_table("assets") as batch:
        batch.drop_constraint("ck_assets_contact_type", type_="check")
        batch.drop_constraint("ck_assets_contact_count", type_="check")
        batch.drop_constraint("ck_assets_coil_voltage_type", type_="check")
        batch.drop_constraint("ck_assets_coil_voltage", type_="check")
        batch.drop_constraint("ck_assets_rated_current", type_="check")
        batch.drop_constraint("ck_assets_breaker_characteristic", type_="check")
        batch.drop_column("contact_type")
        batch.drop_column("contact_count")
        batch.drop_column("coil_voltage_type")
        batch.drop_column("coil_voltage_v")
        batch.drop_column("rated_current_a")
        batch.drop_column("breaker_characteristic")

    with op.batch_alter_table("asset_types") as batch:
        batch.drop_constraint("ck_asset_types_contact_type", type_="check")
        batch.drop_constraint("ck_asset_types_contact_count", type_="check")
        batch.drop_constraint("ck_asset_types_coil_voltage_type", type_="check")
        batch.drop_constraint("ck_asset_types_coil_voltage", type_="check")
        batch.drop_constraint("ck_asset_types_rated_current", type_="check")
        batch.drop_constraint("ck_asset_types_breaker_characteristic", type_="check")
        batch.drop_column("contact_type")
        batch.drop_column("contact_count")
        batch.drop_column("coil_voltage_type")
        batch.drop_column("coil_voltage_v")
        batch.drop_column("rated_current_a")
        batch.drop_column("breaker_characteristic")
