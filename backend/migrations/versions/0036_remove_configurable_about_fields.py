"""Remove obsolete configurable about, imprint and feedback fields.

Revision ID: 0036
Revises: 0035
Create Date: 2026-07-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_COLUMNS = (
    "feedback_folder",
    "feedback_enabled",
    "imprint_free_text",
    "imprint_vat_id",
    "imprint_registry_info",
    "imprint_responsible_person",
    "imprint_phone",
    "imprint_email",
    "imprint_address",
    "imprint_operator_name",
    "license_notice",
    "issue_url",
    "release_url",
    "repository_url",
    "project_website_url",
)


def upgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        for column in _COLUMNS:
            batch.drop_column(column)


def downgrade() -> None:
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
