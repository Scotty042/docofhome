"""Add module visibility settings and optional product images.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_ENABLED_MODULES = (
    '["locations","electrical","assets","master_data","network",'
    '"smart_home","consumption","wiki"]'
)


def upgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        batch.add_column(
            sa.Column(
                "enabled_modules_json",
                sa.String(),
                nullable=False,
                server_default=DEFAULT_ENABLED_MODULES,
            )
        )

    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("image_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.drop_column("image_url")

    with op.batch_alter_table("application_settings") as batch:
        batch.drop_column("enabled_modules_json")
