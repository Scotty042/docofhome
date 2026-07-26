"""Add configurable about-page, imprint and feedback settings.

Revision ID: 0035
Revises: 0034
Create Date: 2026-07-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        batch.add_column(sa.Column("project_website_url", sa.String(length=500)))
        batch.add_column(sa.Column("repository_url", sa.String(length=500)))
        batch.add_column(sa.Column("release_url", sa.String(length=500)))
        batch.add_column(sa.Column("issue_url", sa.String(length=500)))
        batch.add_column(sa.Column("license_notice", sa.String(length=1000)))
        batch.add_column(sa.Column("imprint_operator_name", sa.String(length=200)))
        batch.add_column(sa.Column("imprint_address", sa.Text()))
        batch.add_column(sa.Column("imprint_email", sa.String(length=255)))
        batch.add_column(sa.Column("imprint_phone", sa.String(length=100)))
        batch.add_column(sa.Column("imprint_responsible_person", sa.String(length=200)))
        batch.add_column(sa.Column("imprint_registry_info", sa.String(length=500)))
        batch.add_column(sa.Column("imprint_vat_id", sa.String(length=100)))
        batch.add_column(sa.Column("imprint_free_text", sa.Text()))
        batch.add_column(
            sa.Column(
                "feedback_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(
            sa.Column(
                "feedback_folder",
                sa.String(length=500),
                nullable=False,
                server_default="DocOfHome/Feedback",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        batch.drop_column("feedback_folder")
        batch.drop_column("feedback_enabled")
        batch.drop_column("imprint_free_text")
        batch.drop_column("imprint_vat_id")
        batch.drop_column("imprint_registry_info")
        batch.drop_column("imprint_responsible_person")
        batch.drop_column("imprint_phone")
        batch.drop_column("imprint_email")
        batch.drop_column("imprint_address")
        batch.drop_column("imprint_operator_name")
        batch.drop_column("license_notice")
        batch.drop_column("issue_url")
        batch.drop_column("release_url")
        batch.drop_column("repository_url")
        batch.drop_column("project_website_url")
