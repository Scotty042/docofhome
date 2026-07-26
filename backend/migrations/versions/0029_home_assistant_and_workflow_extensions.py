"""Add HA roles, cabinet side/asset placement, product images and workflow settings.

Revision ID: 0029
Revises: 0028
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

HA_ROLES = (
    "primary_live",
    "total_power",
    "voltage",
    "current",
    "energy",
    "power_l1",
    "power_l2",
    "power_l3",
    "voltage_l1",
    "voltage_l2",
    "voltage_l3",
    "additional",
)


def upgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        batch.add_column(
            sa.Column(
                "online_product_image_search_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    with op.batch_alter_table("products") as batch:
        batch.add_column(
            sa.Column("image_source", sa.String(length=20), nullable=False, server_default="url")
        )
        batch.add_column(sa.Column("image_reference", sa.String(length=1000), nullable=True))
        batch.add_column(
            sa.Column("din_rail_mount", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("module_width", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "ck_products_image_source",
            "image_source IN ('url', 'upload', 'immich', 'online')",
        )
        batch.create_check_constraint(
            "ck_products_module_width",
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
        )
    op.execute(
        sa.text(
            "UPDATE products SET image_source = CASE "
            "WHEN image_url IS NULL OR trim(image_url) = '' THEN 'url' "
            "WHEN image_url LIKE '/api/v1/products/images/%' THEN 'upload' "
            "WHEN image_url LIKE '/api/v1/immich/assets/%' THEN 'immich' "
            "ELSE 'url' END"
        )
    )

    with op.batch_alter_table("home_assistant_asset_links") as batch:
        batch.add_column(
            sa.Column("role", sa.String(length=30), nullable=False, server_default="additional")
        )
        batch.create_check_constraint(
            "ck_home_assistant_asset_links_role",
            "role IN (" + ", ".join(repr(role) for role in HA_ROLES) + ")",
        )
    op.create_index(
        "ix_home_assistant_asset_links_asset_type",
        "home_assistant_asset_links",
        ["asset_id", "object_type"],
    )
    op.create_index(
        "ix_home_assistant_asset_links_asset_role",
        "home_assistant_asset_links",
        ["asset_id", "role"],
    )

    # Replace the old one-position-per-level rule with a level/side model.
    op.drop_index(
        "uq_electrical_distribution_areas_active_position",
        table_name="electrical_distribution_areas",
    )
    # Add the nullable column first. Existing half-width rows must be migrated
    # before the stricter check constraint is created (SQLite batch mode copies
    # existing rows into a replacement table).
    with op.batch_alter_table("electrical_distribution_areas") as batch:
        batch.add_column(sa.Column("side", sa.String(length=10), nullable=True))
    # Existing half-width areas remain visually unchanged on their previous levels.
    op.execute(
        sa.text(
            "UPDATE electrical_distribution_areas SET side = 'left' "
            "WHERE width = 'half' AND side IS NULL"
        )
    )
    with op.batch_alter_table("electrical_distribution_areas") as batch:
        batch.create_check_constraint(
            "ck_electrical_distribution_areas_side",
            "(width = 'full' AND side IS NULL) OR "
            "(width = 'half' AND side IN ('left', 'right'))",
        )
    op.create_index(
        "uq_electrical_distribution_areas_active_full_level",
        "electrical_distribution_areas",
        ["section_id", "position"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND width = 'full'"),
    )
    op.create_index(
        "uq_electrical_distribution_areas_active_half_side",
        "electrical_distribution_areas",
        ["section_id", "position", "side"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND width = 'half'"),
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER IF NOT EXISTS trg_distribution_area_level_insert "
            "BEFORE INSERT ON electrical_distribution_areas "
            "WHEN NEW.deleted_at IS NULL AND EXISTS ("
            "SELECT 1 FROM electrical_distribution_areas existing "
            "WHERE existing.section_id = NEW.section_id "
            "AND existing.position = NEW.position "
            "AND existing.deleted_at IS NULL "
            "AND (NEW.width = 'full' OR existing.width = 'full')) "
            "BEGIN SELECT RAISE(ABORT, 'distribution area level conflict'); END"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER IF NOT EXISTS trg_distribution_area_level_update "
            "BEFORE UPDATE OF section_id, position, width, side, deleted_at "
            "ON electrical_distribution_areas "
            "WHEN NEW.deleted_at IS NULL AND EXISTS ("
            "SELECT 1 FROM electrical_distribution_areas existing "
            "WHERE existing.id <> NEW.id "
            "AND existing.section_id = NEW.section_id "
            "AND existing.position = NEW.position "
            "AND existing.deleted_at IS NULL "
            "AND (NEW.width = 'full' OR existing.width = 'full')) "
            "BEGIN SELECT RAISE(ABORT, 'distribution area level conflict'); END"
        )
    )

    op.create_table(
        "electrical_asset_placements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("area_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("start_position", sa.Integer(), nullable=False),
        sa.Column("module_width", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "row_number >= 1 AND row_number <= 100",
            name="ck_electrical_asset_placements_row",
        ),
        sa.CheckConstraint(
            "start_position >= 1 AND start_position <= 1000",
            name="ck_electrical_asset_placements_start",
        ),
        sa.CheckConstraint(
            "module_width >= 1 AND module_width <= 100",
            name="ck_electrical_asset_placements_width",
        ),
        sa.ForeignKeyConstraint(["distribution_id"], ["electrical_distributions.id"]),
        sa.ForeignKeyConstraint(["area_id"], ["electrical_distribution_areas.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "distribution_id",
        "area_id",
        "asset_id",
        "row_number",
        "start_position",
        "deleted_at",
    ):
        op.create_index(
            f"ix_electrical_asset_placements_{column}",
            "electrical_asset_placements",
            [column],
        )
    op.create_index(
        "uq_electrical_asset_placements_active_asset",
        "electrical_asset_placements",
        ["asset_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_electrical_asset_placements_area_row",
        "electrical_asset_placements",
        ["area_id", "row_number", "start_position"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_electrical_asset_placements_area_row",
        table_name="electrical_asset_placements",
    )
    op.drop_index(
        "uq_electrical_asset_placements_active_asset",
        table_name="electrical_asset_placements",
    )
    for column in reversed(
        (
            "distribution_id",
            "area_id",
            "asset_id",
            "row_number",
            "start_position",
            "deleted_at",
        )
    ):
        op.drop_index(
            f"ix_electrical_asset_placements_{column}",
            table_name="electrical_asset_placements",
        )
    op.drop_table("electrical_asset_placements")

    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_distribution_area_level_update"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_distribution_area_level_insert"))
    op.drop_index(
        "uq_electrical_distribution_areas_active_half_side",
        table_name="electrical_distribution_areas",
    )
    op.drop_index(
        "uq_electrical_distribution_areas_active_full_level",
        table_name="electrical_distribution_areas",
    )
    # Revision 0028 cannot represent two areas on one level. Move right-hand
    # halves to the next available level while preserving every area.
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, section_id, position, side FROM electrical_distribution_areas "
            "WHERE deleted_at IS NULL ORDER BY section_id, position, "
            "CASE side WHEN 'left' THEN 0 WHEN 'right' THEN 1 ELSE 2 END"
        )
    ).mappings().all()
    used: dict[object, set[int]] = {}
    for row in rows:
        section_used = used.setdefault(row["section_id"], set())
        position = int(row["position"])
        if position in section_used:
            candidate = position + 1
            while candidate in section_used and candidate <= 100:
                candidate += 1
            if candidate > 100:
                candidate = 100
                while candidate in section_used and candidate >= 1:
                    candidate -= 1
            if candidate < 1:
                raise RuntimeError("Cannot downgrade cabinet levels without losing an area")
            connection.execute(
                sa.text(
                    "UPDATE electrical_distribution_areas SET position = :position WHERE id = :id"
                ),
                {"position": candidate, "id": row["id"]},
            )
            position = candidate
        section_used.add(position)

    with op.batch_alter_table("electrical_distribution_areas") as batch:
        batch.drop_constraint("ck_electrical_distribution_areas_side", type_="check")
        batch.drop_column("side")
    op.create_index(
        "uq_electrical_distribution_areas_active_position",
        "electrical_distribution_areas",
        ["section_id", "position"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_index(
        "ix_home_assistant_asset_links_asset_role",
        table_name="home_assistant_asset_links",
    )
    op.drop_index(
        "ix_home_assistant_asset_links_asset_type",
        table_name="home_assistant_asset_links",
    )
    with op.batch_alter_table("home_assistant_asset_links") as batch:
        batch.drop_constraint("ck_home_assistant_asset_links_role", type_="check")
        batch.drop_column("role")

    with op.batch_alter_table("products") as batch:
        batch.drop_constraint("ck_products_module_width", type_="check")
        batch.drop_constraint("ck_products_image_source", type_="check")
        batch.drop_column("module_width")
        batch.drop_column("din_rail_mount")
        batch.drop_column("image_reference")
        batch.drop_column("image_source")

    with op.batch_alter_table("application_settings") as batch:
        batch.drop_column("online_product_image_search_enabled")
