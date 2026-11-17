"""Persist the per-interval BCS marker without changing existing time data."""

import sqlalchemy as sa
from alembic import op

revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "work_intervals", sa.Column("bcs", sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade():
    with op.batch_alter_table("work_intervals") as batch:
        batch.drop_column("bcs")
