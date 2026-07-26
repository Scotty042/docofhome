"""Add an optional account identifier to integration settings.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("integration_settings") as batch_op:
        batch_op.add_column(sa.Column("account", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("integration_settings") as batch_op:
        batch_op.drop_column("account")
