"""Create local links from managed Nextcloud documents to domain records.

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("document_path", sa.String(length=1000), nullable=False),
        sa.Column("document_name", sa.String(length=255), nullable=False),
        sa.Column("document_etag", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "target_type IN ('asset', 'location', 'distribution', 'protective_device', 'circuit')",
            name="ck_document_links_target_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_links_target_type", "document_links", ["target_type"])
    op.create_index("ix_document_links_target_id", "document_links", ["target_id"])
    op.create_index("ix_document_links_deleted_at", "document_links", ["deleted_at"])
    op.create_index(
        "uq_document_links_active_target_path",
        "document_links",
        ["target_type", "target_id", "document_path"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_document_links_active_target_path", table_name="document_links")
    op.drop_index("ix_document_links_deleted_at", table_name="document_links")
    op.drop_index("ix_document_links_target_id", table_name="document_links")
    op.drop_index("ix_document_links_target_type", table_name="document_links")
    op.drop_table("document_links")
