"""Create consumption meters, readings, notes and local settings.

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consumption_meters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("meter_type", sa.String(length=30), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("decimals", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("parent_meter_id", sa.Uuid(), nullable=True),
        sa.Column("home_assistant_entity_id", sa.String(length=255), nullable=True),
        sa.Column("water_role", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "meter_type IN ('water', 'electricity_grid', 'electricity_pv', 'gas', 'heat', 'oil', 'other')",
            name="ck_consumption_meters_type",
        ),
        sa.CheckConstraint(
            "water_role IN ('none', 'main', 'eg_component')",
            name="ck_consumption_meters_water_role",
        ),
        sa.CheckConstraint(
            "meter_type = 'water' OR water_role = 'none'",
            name="ck_consumption_meters_water_role_type",
        ),
        sa.CheckConstraint(
            "decimals >= 0 AND decimals <= 6",
            name="ck_consumption_meters_decimals",
        ),
        sa.CheckConstraint("sort_order >= 0", name="ck_consumption_meters_sort_order"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["parent_meter_id"], ["consumption_meters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "deleted_at",
        "name",
        "meter_type",
        "sort_order",
        "serial_number",
        "asset_id",
        "location_id",
        "parent_meter_id",
        "home_assistant_entity_id",
        "water_role",
    ):
        op.create_index(f"ix_consumption_meters_{column}", "consumption_meters", [column])
    op.create_index(
        "uq_consumption_meters_active_name",
        "consumption_meters",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_consumption_meters_active_main_water",
        "consumption_meters",
        ["water_role"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND water_role = 'main'"),
    )

    op.create_table(
        "consumption_readings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("meter_id", sa.Uuid(), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("is_reset", sa.Boolean(), nullable=False),
        sa.Column("immich_asset_id", sa.String(length=36), nullable=True),
        sa.Column("immich_original_file_name", sa.String(length=500), nullable=True),
        sa.CheckConstraint("value >= 0", name="ck_consumption_readings_value"),
        sa.CheckConstraint(
            "source IN ('manual', 'csv', 'legacy_sqlite', 'home_assistant')",
            name="ck_consumption_readings_source",
        ),
        sa.ForeignKeyConstraint(["meter_id"], ["consumption_meters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "meter_id", "measured_at", "source", "is_reset", "immich_asset_id"):
        op.create_index(f"ix_consumption_readings_{column}", "consumption_readings", [column])
    op.create_index(
        "uq_consumption_readings_active_meter_time",
        "consumption_readings",
        ["meter_id", "measured_at"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_consumption_readings_active_time",
        "consumption_readings",
        ["measured_at"],
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "consumption_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("note_date", sa.DateTime(), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "scope IN ('general', 'month', 'year')",
            name="ck_consumption_notes_scope",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "note_date", "scope"):
        op.create_index(f"ix_consumption_notes_{column}", "consumption_notes", [column])
    op.create_index(
        "ix_consumption_notes_active_date",
        "consumption_notes",
        ["note_date"],
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "consumption_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reminder_days", sa.Integer(), nullable=False),
        sa.Column("plausibility_threshold_percent", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "reminder_days >= 1 AND reminder_days <= 3650",
            name="ck_consumption_settings_reminder_days",
        ),
        sa.CheckConstraint(
            "plausibility_threshold_percent >= 100 AND plausibility_threshold_percent <= 10000",
            name="ck_consumption_settings_plausibility_threshold",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        sa.table(
            "consumption_settings",
            sa.column("id", sa.Integer()),
            sa.column("reminder_days", sa.Integer()),
            sa.column("plausibility_threshold_percent", sa.Integer()),
            sa.column("created_at", sa.DateTime()),
            sa.column("updated_at", sa.DateTime()),
        ),
        [
            {
                "id": 1,
                "reminder_days": 31,
                "plausibility_threshold_percent": 150,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("consumption_settings")

    op.drop_index("ix_consumption_notes_active_date", table_name="consumption_notes")
    for column in ("scope", "note_date", "deleted_at"):
        op.drop_index(f"ix_consumption_notes_{column}", table_name="consumption_notes")
    op.drop_table("consumption_notes")

    op.drop_index("ix_consumption_readings_active_time", table_name="consumption_readings")
    op.drop_index("uq_consumption_readings_active_meter_time", table_name="consumption_readings")
    for column in ("immich_asset_id", "is_reset", "source", "measured_at", "meter_id", "deleted_at"):
        op.drop_index(f"ix_consumption_readings_{column}", table_name="consumption_readings")
    op.drop_table("consumption_readings")

    op.drop_index("uq_consumption_meters_active_main_water", table_name="consumption_meters")
    op.drop_index("uq_consumption_meters_active_name", table_name="consumption_meters")
    for column in (
        "water_role",
        "home_assistant_entity_id",
        "parent_meter_id",
        "location_id",
        "asset_id",
        "serial_number",
        "sort_order",
        "meter_type",
        "name",
        "deleted_at",
    ):
        op.drop_index(f"ix_consumption_meters_{column}", table_name="consumption_meters")
    op.drop_table("consumption_meters")
