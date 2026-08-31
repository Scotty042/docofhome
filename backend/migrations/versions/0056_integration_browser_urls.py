"""Separate container API URLs from browser-facing integration URLs.

Revision ID: 0056
Revises: 0055
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0056"
down_revision: str | None = "0055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("integration_settings") as batch:
        batch.add_column(sa.Column("browser_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("integration_settings") as batch:
        batch.drop_column("browser_url")
