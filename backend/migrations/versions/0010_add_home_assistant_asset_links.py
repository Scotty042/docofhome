"""Add Home Assistant object-to-asset links.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "home_assistant_asset_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("object_type", sa.String(length=20), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "object_type IN ('device', 'entity')",
            name="ck_home_assistant_asset_links_object_type",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "object_type",
            "external_id",
            name="uq_home_assistant_asset_links_external_object",
        ),
    )
    op.create_index(
        "ix_home_assistant_asset_links_object_type",
        "home_assistant_asset_links",
        ["object_type"],
    )
    op.create_index(
        "ix_home_assistant_asset_links_external_id",
        "home_assistant_asset_links",
        ["external_id"],
    )
    op.create_index(
        "ix_home_assistant_asset_links_asset_id",
        "home_assistant_asset_links",
        ["asset_id"],
    )


def downgrade() -> None:
    op.drop_table("home_assistant_asset_links")
