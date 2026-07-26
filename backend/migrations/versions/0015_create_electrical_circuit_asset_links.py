"""Connect existing assets to documented electrical circuits.

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "electrical_circuit_asset_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("circuit_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(
            ["circuit_id"],
            ["electrical_circuits.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_electrical_circuit_asset_links_asset_id",
        "electrical_circuit_asset_links",
        ["asset_id"],
    )
    op.create_index(
        "ix_electrical_circuit_asset_links_circuit_id",
        "electrical_circuit_asset_links",
        ["circuit_id"],
    )
    op.create_index(
        "ix_electrical_circuit_asset_links_deleted_at",
        "electrical_circuit_asset_links",
        ["deleted_at"],
    )
    op.create_index(
        "uq_electrical_circuit_asset_links_active",
        "electrical_circuit_asset_links",
        ["circuit_id", "asset_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_electrical_circuit_asset_links_active",
        table_name="electrical_circuit_asset_links",
    )
    op.drop_index(
        "ix_electrical_circuit_asset_links_deleted_at",
        table_name="electrical_circuit_asset_links",
    )
    op.drop_index(
        "ix_electrical_circuit_asset_links_circuit_id",
        table_name="electrical_circuit_asset_links",
    )
    op.drop_index(
        "ix_electrical_circuit_asset_links_asset_id",
        table_name="electrical_circuit_asset_links",
    )
    op.drop_table("electrical_circuit_asset_links")
