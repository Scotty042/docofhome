"""Add the managed Nextcloud document root.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("integration_settings") as batch_op:
        batch_op.add_column(sa.Column("document_root", sa.String(length=500), nullable=True))
    op.execute(
        sa.text(
            "UPDATE integration_settings "
            "SET document_root = 'docofhome/Documents' "
            "WHERE kind = 'nextcloud' AND (document_root IS NULL OR document_root = '')"
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("integration_settings") as batch_op:
        batch_op.drop_column("document_root")
