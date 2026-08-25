"""Create electrical circuits.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "electrical_circuits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("protective_device_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "circuit_number",
            sa.String(length=50, collation="NOCASE"),
            nullable=True,
        ),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["distribution_id"],
            ["electrical_distributions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["protective_device_id"],
            ["electrical_protective_devices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_electrical_circuits_distribution_id",
        "electrical_circuits",
        ["distribution_id"],
    )
    op.create_index(
        "ix_electrical_circuits_protective_device_id",
        "electrical_circuits",
        ["protective_device_id"],
    )
    op.create_index(
        "ix_electrical_circuits_name",
        "electrical_circuits",
        ["name"],
    )
    op.create_index(
        "ix_electrical_circuits_deleted_at",
        "electrical_circuits",
        ["deleted_at"],
    )
    op.create_index(
        "uq_electrical_circuits_active_number",
        "electrical_circuits",
        ["distribution_id", "circuit_number"],
        unique=True,
        sqlite_where=sa.text(
            "deleted_at IS NULL AND circuit_number IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_table("electrical_circuits")
