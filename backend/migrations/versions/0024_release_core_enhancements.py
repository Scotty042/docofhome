"""Add dashboard, recurrence, meter reminder, port, and inventory release features.

Revision ID: 0024
Revises: 0023
"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _recover_batch_table(table_name: str) -> set[str]:
    """Recover safely from SQLite's non-transactional Alembic batch DDL."""

    connection = op.get_bind()
    temporary_name = f"_alembic_tmp_{table_name}"
    inspector = sa.inspect(connection)
    original_exists = inspector.has_table(table_name)
    temporary_exists = inspector.has_table(temporary_name)
    if temporary_exists and original_exists:
        # The canonical table still owns all user data. The temporary table is an
        # incomplete copy left by a failed batch operation and is safe to discard.
        op.execute(sa.text(f'DROP TABLE "{temporary_name}"'))
    elif temporary_exists:
        # The batch already dropped the original but failed before its final rename.
        # Restore the completed copy and let the column checks below skip this step.
        op.execute(sa.text(f'ALTER TABLE "{temporary_name}" RENAME TO "{table_name}"'))
    inspector = sa.inspect(connection)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    return any(
        item["name"] == index_name
        for item in sa.inspect(op.get_bind()).get_indexes(table_name)
    )


def _assert_unique_inventory_numbers() -> None:
    connection = op.get_bind()
    conflicts = connection.execute(
        sa.text(
            """
            SELECT lower(trim(inventory_number)) AS normalized, count(*) AS amount
            FROM assets
            WHERE inventory_number IS NOT NULL AND trim(inventory_number) <> ''
            GROUP BY lower(trim(inventory_number))
            HAVING count(*) > 1
            """
        )
    ).all()
    if conflicts:
        values = ", ".join(str(row.normalized) for row in conflicts[:10])
        raise RuntimeError(
            "Duplicate inventory numbers must be resolved before upgrading: "
            f"{values}"
        )


def upgrade() -> None:
    work_columns = _recover_batch_table("work_items")
    if "recurrence_mode" not in work_columns:
        with op.batch_alter_table("work_items") as batch:
            batch.add_column(
                sa.Column(
                    "recurrence_mode",
                    sa.String(length=20),
                    nullable=False,
                    server_default="none",
                )
            )
            batch.add_column(sa.Column("calendar_months", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("calendar_day", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("calendar_month", sa.Integer(), nullable=True))
            batch.add_column(
                sa.Column(
                    "calendar_last_day",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
            batch.create_index("ix_work_items_recurrence_mode", ["recurrence_mode"], unique=False)
            batch.create_check_constraint(
                "ck_work_items_recurrence_mode",
                "recurrence_mode IN ('none', 'interval', 'calendar')",
            )
            batch.create_check_constraint(
                "ck_work_items_calendar_months",
                "calendar_months IS NULL OR calendar_months IN (1, 2, 3, 6, 12)",
            )
            batch.create_check_constraint(
                "ck_work_items_calendar_day",
                "calendar_day IS NULL OR (calendar_day >= 1 AND calendar_day <= 31)",
            )
            batch.create_check_constraint(
                "ck_work_items_calendar_month",
                "calendar_month IS NULL OR (calendar_month >= 1 AND calendar_month <= 12)",
            )
    op.execute(
        """
        UPDATE work_items
        SET recurrence_mode = 'interval'
        WHERE recurrence_days IS NOT NULL
        """
    )

    consumption_columns = _recover_batch_table("consumption_meters")
    if "primary_for_dashboard" not in consumption_columns:
        with op.batch_alter_table("consumption_meters") as batch:
            batch.add_column(
                sa.Column(
                    "primary_for_dashboard",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
            batch.add_column(sa.Column("reading_schedule_day", sa.Integer(), nullable=True))
            batch.add_column(
                sa.Column(
                    "reading_schedule_last_day",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
            batch.add_column(
                sa.Column("reminder_days_json", sa.Text(), nullable=False, server_default="[]")
            )
            batch.create_index(
                "ix_consumption_meters_primary_for_dashboard",
                ["primary_for_dashboard"],
                unique=False,
            )
            batch.create_check_constraint(
                "ck_consumption_meters_schedule_day",
                "reading_schedule_day IS NULL OR "
                "(reading_schedule_day >= 1 AND reading_schedule_day <= 31)",
            )
            batch.create_check_constraint(
                "ck_consumption_meters_schedule_choice",
                "NOT (reading_schedule_last_day = 1 AND reading_schedule_day IS NOT NULL)",
            )
    op.execute(
        """
        UPDATE consumption_meters
        SET primary_for_dashboard = 1
        WHERE deleted_at IS NULL AND meter_type = 'water' AND water_role = 'main'
        """
    )
    for meter_type in ("electricity_grid", "gas"):
        op.execute(
            sa.text(
                """
                UPDATE consumption_meters
                SET primary_for_dashboard = 1
                WHERE deleted_at IS NULL
                  AND meter_type = :meter_type
                  AND (
                    SELECT count(*)
                    FROM consumption_meters AS candidates
                    WHERE candidates.deleted_at IS NULL
                      AND candidates.meter_type = :meter_type
                  ) = 1
                """
            ).bindparams(meter_type=meter_type)
        )
    if not _has_index("consumption_meters", "uq_consumption_meters_active_primary_type"):
        op.create_index(
            "uq_consumption_meters_active_primary_type",
            "consumption_meters",
            ["meter_type"],
            unique=True,
            sqlite_where=sa.text("deleted_at IS NULL AND primary_for_dashboard = 1"),
        )

    interface_columns = _recover_batch_table("network_interfaces")
    if "autogenerated" not in interface_columns:
        with op.batch_alter_table("network_interfaces") as batch:
            batch.add_column(
                sa.Column("autogenerated", sa.Boolean(), nullable=False, server_default=sa.false())
            )
            batch.add_column(sa.Column("port_group", sa.String(length=30), nullable=True))
            batch.add_column(
                sa.Column(
                    "manually_customized",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
            batch.create_index(
                "ix_network_interfaces_autogenerated",
                ["autogenerated"],
                unique=False,
            )

    _assert_unique_inventory_numbers()
    if not _has_index("assets", "uq_assets_inventory_number_global"):
        op.create_index(
            "uq_assets_inventory_number_global",
            "assets",
            ["inventory_number"],
            unique=True,
            sqlite_where=sa.text(
                "inventory_number IS NOT NULL AND trim(inventory_number) <> ''"
            ),
        )

    dashboard_exists = sa.inspect(op.get_bind()).has_table("dashboard_settings")
    if not dashboard_exists:
        op.create_table(
            "dashboard_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("layout_json", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    dashboard = sa.table(
        "dashboard_settings",
        sa.column("id", sa.Integer()),
        sa.column("layout_json", sa.Text()),
        sa.column("updated_at", sa.DateTime()),
    )
    dashboard_count = op.get_bind().execute(
        sa.text("SELECT count(*) FROM dashboard_settings WHERE id = 1")
    ).scalar_one()
    if dashboard_count == 0:
        op.bulk_insert(
            dashboard,
            [
                {
                    "id": 1,
                    "layout_json": json.dumps(
                        [
                            {"id": "system", "visible": True},
                            {"id": "documentation", "visible": True},
                            {"id": "consumption_comparison", "visible": True},
                            {"id": "maintenance", "visible": True},
                            {"id": "quality", "visible": True},
                            {"id": "network", "visible": True},
                        ],
                        separators=(",", ":"),
                    ),
                    "updated_at": datetime.now(UTC).replace(tzinfo=None),
                }
            ],
        )


def downgrade() -> None:
    op.drop_table("dashboard_settings")
    op.drop_index("uq_assets_inventory_number_global", table_name="assets")
    with op.batch_alter_table("network_interfaces") as batch:
        batch.drop_index("ix_network_interfaces_autogenerated")
        batch.drop_column("manually_customized")
        batch.drop_column("port_group")
        batch.drop_column("autogenerated")
    op.drop_index(
        "uq_consumption_meters_active_primary_type",
        table_name="consumption_meters",
    )
    with op.batch_alter_table("consumption_meters") as batch:
        batch.drop_constraint("ck_consumption_meters_schedule_choice", type_="check")
        batch.drop_constraint("ck_consumption_meters_schedule_day", type_="check")
        batch.drop_index("ix_consumption_meters_primary_for_dashboard")
        batch.drop_column("reminder_days_json")
        batch.drop_column("reading_schedule_last_day")
        batch.drop_column("reading_schedule_day")
        batch.drop_column("primary_for_dashboard")
    with op.batch_alter_table("work_items") as batch:
        batch.drop_constraint("ck_work_items_calendar_month", type_="check")
        batch.drop_constraint("ck_work_items_calendar_day", type_="check")
        batch.drop_constraint("ck_work_items_calendar_months", type_="check")
        batch.drop_constraint("ck_work_items_recurrence_mode", type_="check")
        batch.drop_index("ix_work_items_recurrence_mode")
        batch.drop_column("calendar_last_day")
        batch.drop_column("calendar_month")
        batch.drop_column("calendar_day")
        batch.drop_column("calendar_months")
        batch.drop_column("recurrence_mode")
