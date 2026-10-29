"""Persistent push delivery claims and status."""

import sqlalchemy as sa
from alembic import op

revision = "0060"
down_revision = "0059"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "push_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("delivery_key", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("detail", sa.String(300)),
        sa.Column("last_attempt_at", sa.DateTime()),
        sa.Column("next_retry_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("provider IN ('pushover','ntfy')", name="ck_push_provider"),
        sa.CheckConstraint(
            "status IN ('pending','sending','sent','failed')", name="ck_push_status"
        ),
    )
    op.create_index(
        "ix_push_deliveries_delivery_key", "push_deliveries", ["delivery_key"], unique=True
    )


def downgrade():
    op.drop_table("push_deliveries")
