"""Create electrical distribution and protective-device roles.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "electrical_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "role IN ('distribution', 'protective_device')",
            name="ck_electrical_components_role",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_electrical_components_asset_id", "electrical_components", ["asset_id"])
    op.create_index("ix_electrical_components_role", "electrical_components", ["role"])
    op.create_index(
        "ix_electrical_components_deleted_at",
        "electrical_components",
        ["deleted_at"],
    )
    op.create_index(
        "uq_electrical_components_active_asset",
        "electrical_components",
        ["asset_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "electrical_distributions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_distribution_id", sa.Uuid(), nullable=True),
        sa.Column("distribution_type", sa.String(length=20), nullable=False),
        sa.Column("designation", sa.String(length=150), nullable=True),
        sa.Column("rows", sa.Integer(), nullable=True),
        sa.Column("modules_per_row", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.CheckConstraint(
            "(distribution_type = 'main' AND parent_distribution_id IS NULL) OR "
            "(distribution_type = 'sub' AND parent_distribution_id IS NOT NULL)",
            name="ck_electrical_distributions_type_parent",
        ),
        sa.CheckConstraint(
            "rows IS NULL OR (rows >= 1 AND rows <= 100)",
            name="ck_electrical_distributions_rows",
        ),
        sa.CheckConstraint(
            "modules_per_row IS NULL OR "
            "(modules_per_row >= 1 AND modules_per_row <= 1000)",
            name="ck_electrical_distributions_modules",
        ),
        sa.ForeignKeyConstraint(["id"], ["electrical_components.id"]),
        sa.ForeignKeyConstraint(
            ["parent_distribution_id"],
            ["electrical_distributions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_electrical_distributions_parent_distribution_id",
        "electrical_distributions",
        ["parent_distribution_id"],
    )
    op.create_index(
        "ix_electrical_distributions_distribution_type",
        "electrical_distributions",
        ["distribution_type"],
    )
    op.create_index(
        "ix_electrical_distributions_designation",
        "electrical_distributions",
        ["designation"],
    )

    op.create_table(
        "electrical_protective_devices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("device_type", sa.String(length=20), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("start_position", sa.Integer(), nullable=True),
        sa.Column("module_width", sa.Integer(), nullable=True),
        sa.Column("rated_current_a", sa.Float(), nullable=True),
        sa.Column("residual_current_ma", sa.Float(), nullable=True),
        sa.Column("characteristic", sa.String(length=30), nullable=True),
        sa.Column("poles", sa.Integer(), nullable=True),
        sa.Column("breaking_capacity_ka", sa.Float(), nullable=True),
        sa.Column("rcd_type", sa.String(length=80), nullable=True),
        sa.Column("fuse_type", sa.String(length=80), nullable=True),
        sa.Column("spd_type", sa.String(length=80), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.CheckConstraint(
            "device_type IN ('fuse', 'rcd', 'mcb', 'rcbo', 'spd')",
            name="ck_electrical_protective_devices_type",
        ),
        sa.CheckConstraint(
            "(row_number IS NULL AND start_position IS NULL AND module_width IS NULL) OR "
            "(row_number IS NOT NULL AND start_position IS NOT NULL AND module_width IS NOT NULL)",
            name="ck_electrical_protective_devices_position_group",
        ),
        sa.CheckConstraint(
            "row_number IS NULL OR (row_number >= 1 AND row_number <= 100)",
            name="ck_electrical_protective_devices_row",
        ),
        sa.CheckConstraint(
            "start_position IS NULL OR (start_position >= 1 AND start_position <= 1000)",
            name="ck_electrical_protective_devices_start",
        ),
        sa.CheckConstraint(
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
            name="ck_electrical_protective_devices_width",
        ),
        sa.CheckConstraint(
            "rated_current_a IS NULL OR "
            "(rated_current_a > 0 AND rated_current_a <= 10000)",
            name="ck_electrical_protective_devices_current",
        ),
        sa.CheckConstraint(
            "residual_current_ma IS NULL OR "
            "(residual_current_ma > 0 AND residual_current_ma <= 100000)",
            name="ck_electrical_protective_devices_residual",
        ),
        sa.CheckConstraint(
            "poles IS NULL OR (poles >= 1 AND poles <= 12)",
            name="ck_electrical_protective_devices_poles",
        ),
        sa.CheckConstraint(
            "breaking_capacity_ka IS NULL OR "
            "(breaking_capacity_ka > 0 AND breaking_capacity_ka <= 1000)",
            name="ck_electrical_protective_devices_breaking_capacity",
        ),
        sa.ForeignKeyConstraint(["id"], ["electrical_components.id"]),
        sa.ForeignKeyConstraint(
            ["distribution_id"],
            ["electrical_distributions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("distribution_id", "device_type", "row_number", "start_position"):
        op.create_index(
            f"ix_electrical_protective_devices_{column}",
            "electrical_protective_devices",
            [column],
        )

    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        triggers = (
            "CREATE TRIGGER trg_electrical_component_asset_immutable "
            "BEFORE UPDATE OF asset_id ON electrical_components "
            "WHEN NEW.asset_id <> OLD.asset_id BEGIN "
            "SELECT RAISE(ABORT, 'electrical role asset is immutable'); END",
            "CREATE TRIGGER trg_electrical_distribution_role_insert "
            "BEFORE INSERT ON electrical_distributions "
            "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
            "WHERE id = NEW.id AND role = 'distribution') BEGIN "
            "SELECT RAISE(ABORT, 'electrical distribution role mismatch'); END",
            "CREATE TRIGGER trg_electrical_distribution_role_update "
            "BEFORE UPDATE OF id ON electrical_distributions "
            "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
            "WHERE id = NEW.id AND role = 'distribution') BEGIN "
            "SELECT RAISE(ABORT, 'electrical distribution role mismatch'); END",
            "CREATE TRIGGER trg_electrical_device_role_insert "
            "BEFORE INSERT ON electrical_protective_devices "
            "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
            "WHERE id = NEW.id AND role = 'protective_device') BEGIN "
            "SELECT RAISE(ABORT, 'electrical protective-device role mismatch'); END",
            "CREATE TRIGGER trg_electrical_device_role_update "
            "BEFORE UPDATE OF id ON electrical_protective_devices "
            "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
            "WHERE id = NEW.id AND role = 'protective_device') BEGIN "
            "SELECT RAISE(ABORT, 'electrical protective-device role mismatch'); END",
            "CREATE TRIGGER trg_electrical_distribution_capacity_guard "
            "BEFORE UPDATE OF rows, modules_per_row ON electrical_distributions "
            "WHEN EXISTS ("
            "SELECT 1 FROM electrical_protective_devices device "
            "JOIN electrical_components component ON component.id = device.id "
            "WHERE device.distribution_id = OLD.id "
            "AND component.deleted_at IS NULL "
            "AND device.row_number IS NOT NULL "
            "AND ((NEW.rows IS NOT NULL AND device.row_number > NEW.rows) "
            "OR (NEW.modules_per_row IS NOT NULL "
            "AND device.start_position + device.module_width - 1 > NEW.modules_per_row))"
            ") BEGIN SELECT RAISE(ABORT, "
            "'distribution capacity conflicts with active protective devices'); END",
        )
        for statement in triggers:
            connection.exec_driver_sql(statement)
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations after electrical migration: {violations}")


def downgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        for trigger in (
            "trg_electrical_distribution_capacity_guard",
            "trg_electrical_device_role_update",
            "trg_electrical_device_role_insert",
            "trg_electrical_distribution_role_update",
            "trg_electrical_distribution_role_insert",
            "trg_electrical_component_asset_immutable",
        ):
            connection.exec_driver_sql(f"DROP TRIGGER IF EXISTS {trigger}")

    op.drop_table("electrical_protective_devices")
    op.drop_table("electrical_distributions")
    op.drop_table("electrical_components")

    if connection.dialect.name == "sqlite":
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(
                f"Foreign-key violations after electrical downgrade: {violations}"
            )
