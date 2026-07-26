"""Create first-run and integration settings tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("installation_name", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("theme", sa.String(length=20), nullable=False),
        sa.Column("setup_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "integration_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("base_url", sa.String(length=2048), nullable=True),
        sa.Column("secret", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_integration_settings_kind",
        "integration_settings",
        ["kind"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_integration_settings_kind", table_name="integration_settings")
    op.drop_table("integration_settings")
    op.drop_table("application_settings")
