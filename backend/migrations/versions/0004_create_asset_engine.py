"""Create the asset engine tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _record_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "asset_types",
        *_record_columns(),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("icon", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_types_deleted_at", "asset_types", ["deleted_at"])
    op.create_index("ix_asset_types_name", "asset_types", ["name"])

    op.create_table(
        "products",
        *_record_columns(),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("manufacturer", sa.String(length=150), nullable=True),
        sa.Column("model_number", sa.String(length=150), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("asset_type_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["asset_type_id"], ["asset_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "name", "manufacturer", "model_number", "asset_type_id"):
        op.create_index(f"ix_products_{column}", "products", [column])

    op.create_table(
        "locations",
        *_record_columns(),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "name", "parent_id"):
        op.create_index(f"ix_locations_{column}", "locations", [column])

    op.create_table(
        "labels",
        *_record_columns(),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_labels_deleted_at", "labels", ["deleted_at"])
    op.create_index("ix_labels_name", "labels", ["name"])

    op.create_table(
        "assets",
        *_record_columns(),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("asset_type_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("inventory_number", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["asset_type_id"], ["asset_types.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "deleted_at",
        "name",
        "asset_type_id",
        "product_id",
        "location_id",
        "serial_number",
        "inventory_number",
        "status",
    ):
        op.create_index(f"ix_assets_{column}", "assets", [column])

    op.create_table(
        "asset_label_links",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"]),
        sa.PrimaryKeyConstraint("asset_id", "label_id"),
    )

    op.create_table(
        "relationships",
        *_record_columns(),
        sa.Column("source_asset_id", sa.Uuid(), nullable=False),
        sa.Column("target_asset_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["source_asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["target_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "source_asset_id", "target_asset_id", "relationship_type"):
        op.create_index(f"ix_relationships_{column}", "relationships", [column])


def downgrade() -> None:
    op.drop_table("relationships")
    op.drop_table("asset_label_links")
    op.drop_table("assets")
    op.drop_table("labels")
    op.drop_table("locations")
    op.drop_table("products")
    op.drop_table("asset_types")
