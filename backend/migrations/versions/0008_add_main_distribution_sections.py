"""Add optional fields and areas for structured main distributions.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("electrical_distributions") as batch:
        batch.add_column(
            sa.Column(
                "layout_mode",
                sa.String(length=20),
                nullable=False,
                server_default="rows",
            )
        )
        batch.create_check_constraint(
            "ck_electrical_distributions_layout_mode",
            "layout_mode IN ('rows', 'sections')",
        )
        batch.create_check_constraint(
            "ck_electrical_distributions_sub_rows_layout",
            "distribution_type = 'main' OR layout_mode = 'rows'",
        )
        batch.create_check_constraint(
            "ck_electrical_distributions_section_capacity",
            "layout_mode = 'rows' OR (rows IS NULL AND modules_per_row IS NULL)",
        )
        batch.create_index(
            "ix_electrical_distributions_layout_mode",
            ["layout_mode"],
            unique=False,
        )

    op.create_table(
        "electrical_distribution_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "position >= 1 AND position <= 50",
            name="ck_electrical_distribution_sections_position",
        ),
        sa.ForeignKeyConstraint(
            ["distribution_id"],
            ["electrical_distributions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_electrical_distribution_sections_distribution_id",
        "electrical_distribution_sections",
        ["distribution_id"],
    )
    op.create_index(
        "ix_electrical_distribution_sections_deleted_at",
        "electrical_distribution_sections",
        ["deleted_at"],
    )
    op.create_index(
        "uq_electrical_distribution_sections_active_position",
        "electrical_distribution_sections",
        ["distribution_id", "position"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "electrical_distribution_areas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("area_type", sa.String(length=30), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("rows", sa.Integer(), nullable=True),
        sa.Column("modules_per_row", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "area_type IN ('device_rows', 'meter', 'connection', 'technology', 'reserve', 'cover')",
            name="ck_electrical_distribution_areas_type",
        ),
        sa.CheckConstraint(
            "position >= 1 AND position <= 100",
            name="ck_electrical_distribution_areas_position",
        ),
        sa.CheckConstraint(
            "rows IS NULL OR (rows >= 1 AND rows <= 100)",
            name="ck_electrical_distribution_areas_rows",
        ),
        sa.CheckConstraint(
            "modules_per_row IS NULL OR (modules_per_row >= 1 AND modules_per_row <= 1000)",
            name="ck_electrical_distribution_areas_modules",
        ),
        sa.CheckConstraint(
            "area_type = 'device_rows' OR (rows IS NULL AND modules_per_row IS NULL)",
            name="ck_electrical_distribution_areas_capacity_type",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["electrical_distribution_sections.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_electrical_distribution_areas_section_id",
        "electrical_distribution_areas",
        ["section_id"],
    )
    op.create_index(
        "ix_electrical_distribution_areas_area_type",
        "electrical_distribution_areas",
        ["area_type"],
    )
    op.create_index(
        "ix_electrical_distribution_areas_deleted_at",
        "electrical_distribution_areas",
        ["deleted_at"],
    )
    op.create_index(
        "uq_electrical_distribution_areas_active_position",
        "electrical_distribution_areas",
        ["section_id", "position"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    with op.batch_alter_table("electrical_protective_devices") as batch:
        batch.add_column(sa.Column("area_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_electrical_protective_devices_area_id",
            "electrical_distribution_areas",
            ["area_id"],
            ["id"],
        )
        batch.create_index(
            "ix_electrical_protective_devices_area_id",
            ["area_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("electrical_protective_devices") as batch:
        batch.drop_index("ix_electrical_protective_devices_area_id")
        batch.drop_constraint(
            "fk_electrical_protective_devices_area_id",
            type_="foreignkey",
        )
        batch.drop_column("area_id")

    op.drop_index(
        "uq_electrical_distribution_areas_active_position",
        table_name="electrical_distribution_areas",
    )
    op.drop_index(
        "ix_electrical_distribution_areas_deleted_at",
        table_name="electrical_distribution_areas",
    )
    op.drop_index(
        "ix_electrical_distribution_areas_area_type",
        table_name="electrical_distribution_areas",
    )
    op.drop_index(
        "ix_electrical_distribution_areas_section_id",
        table_name="electrical_distribution_areas",
    )
    op.drop_table("electrical_distribution_areas")

    op.drop_index(
        "uq_electrical_distribution_sections_active_position",
        table_name="electrical_distribution_sections",
    )
    op.drop_index(
        "ix_electrical_distribution_sections_deleted_at",
        table_name="electrical_distribution_sections",
    )
    op.drop_index(
        "ix_electrical_distribution_sections_distribution_id",
        table_name="electrical_distribution_sections",
    )
    op.drop_table("electrical_distribution_sections")

    with op.batch_alter_table("electrical_distributions") as batch:
        batch.drop_index("ix_electrical_distributions_layout_mode")
        batch.drop_constraint(
            "ck_electrical_distributions_section_capacity",
            type_="check",
        )
        batch.drop_constraint(
            "ck_electrical_distributions_sub_rows_layout",
            type_="check",
        )
        batch.drop_constraint(
            "ck_electrical_distributions_layout_mode",
            type_="check",
        )
        batch.drop_column("layout_mode")
