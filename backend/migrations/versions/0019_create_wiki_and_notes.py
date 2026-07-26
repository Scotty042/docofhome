"""Create hierarchical wiki pages and target-bound notes.

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "sort_order >= 0 AND sort_order <= 100000",
            name="ck_wiki_pages_sort_order",
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["wiki_pages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wiki_pages_parent_id", "wiki_pages", ["parent_id"])
    op.create_index("ix_wiki_pages_title", "wiki_pages", ["title"])
    op.create_index("ix_wiki_pages_slug", "wiki_pages", ["slug"])
    op.create_index("ix_wiki_pages_sort_order", "wiki_pages", ["sort_order"])
    op.create_index("ix_wiki_pages_deleted_at", "wiki_pages", ["deleted_at"])
    op.create_index(
        "uq_wiki_pages_active_slug",
        "wiki_pages",
        ["slug"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "domain_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "target_type IN ('asset', 'location', 'distribution', "
            "'protective_device', 'circuit')",
            name="ck_domain_notes_target_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_notes_target_type", "domain_notes", ["target_type"])
    op.create_index("ix_domain_notes_target_id", "domain_notes", ["target_id"])
    op.create_index("ix_domain_notes_deleted_at", "domain_notes", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_domain_notes_deleted_at", table_name="domain_notes")
    op.drop_index("ix_domain_notes_target_id", table_name="domain_notes")
    op.drop_index("ix_domain_notes_target_type", table_name="domain_notes")
    op.drop_table("domain_notes")
    op.drop_index("uq_wiki_pages_active_slug", table_name="wiki_pages")
    op.drop_index("ix_wiki_pages_deleted_at", table_name="wiki_pages")
    op.drop_index("ix_wiki_pages_sort_order", table_name="wiki_pages")
    op.drop_index("ix_wiki_pages_slug", table_name="wiki_pages")
    op.drop_index("ix_wiki_pages_title", table_name="wiki_pages")
    op.drop_index("ix_wiki_pages_parent_id", table_name="wiki_pages")
    op.drop_table("wiki_pages")
