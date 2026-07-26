"""Add optional DIN widths to asset types and assets.

Revision ID: 0032
Revises: 0031
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("asset_types") as batch:
        batch.add_column(sa.Column("module_width", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "ck_asset_types_module_width",
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
        )

    with op.batch_alter_table("assets") as batch:
        batch.add_column(sa.Column("module_width", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "ck_assets_module_width",
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
        )


def downgrade() -> None:
    with op.batch_alter_table("assets") as batch:
        batch.drop_constraint("ck_assets_module_width", type_="check")
        batch.drop_column("module_width")

    with op.batch_alter_table("asset_types") as batch:
        batch.drop_constraint("ck_asset_types_module_width", type_="check")
        batch.drop_column("module_width")
