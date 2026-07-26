"""Add resumable guided setup drafts.

Revision ID: 0026
Revises: 0025
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guided_setup_drafts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "current_step >= 1 AND current_step <= 11",
            name="ck_guided_setup_drafts_step",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'applied')",
            name="ck_guided_setup_drafts_status",
        ),
    )
    op.create_index(
        "ix_guided_setup_drafts_status",
        "guided_setup_drafts",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("guided_setup_drafts")
