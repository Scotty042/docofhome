"""Add simple FI groups, N-rail assignments and busbar phase patterns.

Revision ID: 0034
Revises: 0033
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.add_column(sa.Column("linked_rcd_device_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("start_phase", sa.String(length=2), nullable=True))
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_start_phase",
            "start_phase IS NULL OR start_phase IN ('L1', 'L2', 'L3')",
        )
        batch.create_foreign_key(
            "fk_electrical_cabinet_components_linked_rcd",
            "electrical_protective_devices",
            ["linked_rcd_device_id"],
            ["id"],
        )
    op.create_index(
        "ix_electrical_cabinet_components_linked_rcd_device_id",
        "electrical_cabinet_components",
        ["linked_rcd_device_id"],
    )

    with op.batch_alter_table("electrical_protective_devices") as batch:
        batch.add_column(sa.Column("assigned_rcd_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("neutral_rail_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_electrical_protective_devices_assigned_rcd",
            "electrical_protective_devices",
            ["assigned_rcd_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_electrical_protective_devices_neutral_rail",
            "electrical_cabinet_components",
            ["neutral_rail_id"],
            ["id"],
        )
    op.create_index(
        "ix_electrical_protective_devices_assigned_rcd_id",
        "electrical_protective_devices",
        ["assigned_rcd_id"],
    )
    op.create_index(
        "ix_electrical_protective_devices_neutral_rail_id",
        "electrical_protective_devices",
        ["neutral_rail_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_electrical_protective_devices_neutral_rail_id",
        table_name="electrical_protective_devices",
    )
    op.drop_index(
        "ix_electrical_protective_devices_assigned_rcd_id",
        table_name="electrical_protective_devices",
    )
    with op.batch_alter_table("electrical_protective_devices") as batch:
        batch.drop_constraint(
            "fk_electrical_protective_devices_neutral_rail", type_="foreignkey"
        )
        batch.drop_constraint(
            "fk_electrical_protective_devices_assigned_rcd", type_="foreignkey"
        )
        batch.drop_column("neutral_rail_id")
        batch.drop_column("assigned_rcd_id")

    op.drop_index(
        "ix_electrical_cabinet_components_linked_rcd_device_id",
        table_name="electrical_cabinet_components",
    )
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.drop_constraint(
            "fk_electrical_cabinet_components_linked_rcd", type_="foreignkey"
        )
        batch.drop_constraint(
            "ck_electrical_cabinet_components_start_phase", type_="check"
        )
        batch.drop_column("start_phase")
        batch.drop_column("linked_rcd_device_id")
