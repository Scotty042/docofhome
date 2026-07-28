"""Allow phase and neutral rails to reference FI/RCD DIN Assets.

Revision ID: 0047
Revises: 0046
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0047"
down_revision: str | None = "0046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.add_column(sa.Column("linked_rcd_asset_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_electrical_cabinet_components_linked_rcd_asset",
            "assets",
            ["linked_rcd_asset_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_single_rcd_reference",
            "linked_rcd_device_id IS NULL OR linked_rcd_asset_id IS NULL",
        )
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_rcd_asset_link_type",
            "linked_rcd_asset_id IS NULL OR component_type IN ('phase_rail', 'neutral_rail')",
        )
    op.create_index(
        "ix_electrical_cabinet_components_linked_rcd_asset_id",
        "electrical_cabinet_components",
        ["linked_rcd_asset_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_electrical_cabinet_components_linked_rcd_asset_id",
        table_name="electrical_cabinet_components",
    )
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.drop_constraint(
            "ck_electrical_cabinet_components_rcd_asset_link_type", type_="check"
        )
        batch.drop_constraint(
            "ck_electrical_cabinet_components_single_rcd_reference", type_="check"
        )
        batch.drop_constraint(
            "fk_electrical_cabinet_components_linked_rcd_asset", type_="foreignkey"
        )
        batch.drop_column("linked_rcd_asset_id")
