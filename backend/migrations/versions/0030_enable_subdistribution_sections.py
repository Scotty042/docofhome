"""Allow structured field layouts for subdistributions.

Revision ID: 0030
Revises: 0029
Create Date: 2026-07-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("electrical_distributions") as batch:
        batch.drop_constraint(
            "ck_electrical_distributions_sub_rows_layout",
            type_="check",
        )


def downgrade() -> None:
    # Structured subdistributions cannot be represented by the previous schema.
    # Convert only their layout mode; the section/area records remain available
    # and become usable again after upgrading to 0030.
    op.execute(
        "UPDATE electrical_distributions "
        "SET layout_mode = 'rows' "
        "WHERE distribution_type = 'sub' AND layout_mode = 'sections'"
    )
    with op.batch_alter_table("electrical_distributions") as batch:
        batch.create_check_constraint(
            "ck_electrical_distributions_sub_rows_layout",
            "distribution_type = 'main' OR layout_mode = 'rows'",
        )
