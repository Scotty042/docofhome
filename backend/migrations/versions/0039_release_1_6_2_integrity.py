"""Release 1.6.2 integrity corrections.

Revision ID: 0039
Revises: 0038
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("work_items") as batch:
        batch.add_column(sa.Column("automation_key", sa.String(length=255)))
        batch.create_index(
            "uq_work_items_automation_key",
            ["automation_key"],
            unique=True,
            sqlite_where=sa.text("automation_key IS NOT NULL AND deleted_at IS NULL"),
        )

    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.add_column(sa.Column("mounting_side", sa.String(length=10)))
        batch.create_check_constraint(
            "ck_electrical_cabinet_components_mounting_side",
            "mounting_side IS NULL OR mounting_side IN ('above', 'below')",
        )
    op.execute(
        "UPDATE electrical_cabinet_components SET mounting_side='below' "
        "WHERE component_type IN ('busbar', 'phase_rail')"
    )

    with op.batch_alter_table("electrical_distributions") as batch:
        batch.drop_constraint("ck_electrical_distributions_layout_mode", type_="check")
        batch.create_check_constraint(
            "ck_electrical_distributions_layout_mode",
            "layout_mode IN ('rows', 'sections', 'junction_box')",
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE electrical_distributions SET layout_mode='rows' "
            "WHERE layout_mode='junction_box'"
        )
    )
    with op.batch_alter_table("electrical_distributions") as batch:
        batch.drop_constraint("ck_electrical_distributions_layout_mode", type_="check")
        batch.create_check_constraint(
            "ck_electrical_distributions_layout_mode",
            "layout_mode IN ('rows', 'sections')",
        )
    with op.batch_alter_table("electrical_cabinet_components") as batch:
        batch.drop_constraint(
            "ck_electrical_cabinet_components_mounting_side",
            type_="check",
        )
        batch.drop_column("mounting_side")
    with op.batch_alter_table("work_items") as batch:
        batch.drop_index("uq_work_items_automation_key")
        batch.drop_column("automation_key")
