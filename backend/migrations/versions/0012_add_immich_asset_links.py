"""Add read-only Immich image links for Tectoryn Assets.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "immich_asset_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("immich_asset_id", sa.String(length=36), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column("file_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(trim(immich_asset_id)) = 36",
            name="ck_immich_asset_links_external_id",
        ),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_immich_asset_links_width"),
        sa.CheckConstraint("height IS NULL OR height > 0", name="ck_immich_asset_links_height"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id",
            "immich_asset_id",
            name="uq_immich_asset_links_asset_external",
        ),
    )
    op.create_index("ix_immich_asset_links_asset_id", "immich_asset_links", ["asset_id"])
    op.create_index(
        "ix_immich_asset_links_immich_asset_id",
        "immich_asset_links",
        ["immich_asset_id"],
    )


def downgrade() -> None:
    op.drop_table("immich_asset_links")
