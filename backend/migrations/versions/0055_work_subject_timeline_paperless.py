"""Work subject profiles, activity timeline categories and Paperless links.

Revision ID: 0055
Revises: 0054
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0055"
down_revision: str | None = "0054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ACTIVITY_KIND_CHECK = (
    "activity_kind IN ('general', 'maintenance', 'inspection', 'repair', "
    "'measurement', 'vaccination', 'appointment', 'official_inspection', "
    "'chimney_sweep', 'service', 'other')"
)


def upgrade() -> None:
    with op.batch_alter_table("work_subjects") as batch:
        batch.add_column(
            sa.Column("profile_json", sa.Text(), nullable=False, server_default="{}")
        )

    with op.batch_alter_table("work_items") as batch:
        batch.add_column(
            sa.Column(
                "activity_kind",
                sa.String(length=30),
                nullable=False,
                server_default="general",
            )
        )
        batch.create_index("ix_work_items_activity_kind", ["activity_kind"], unique=False)
        batch.create_check_constraint("ck_work_items_activity_kind", ACTIVITY_KIND_CHECK)

    op.create_table(
        "work_item_event_paperless_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("created_date", sa.String(length=40), nullable=True),
        sa.Column("original_file_name", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["work_item_events.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "document_id",
            name="uq_work_event_paperless_document",
        ),
    )
    op.create_index(
        "ix_work_item_event_paperless_links_event_id",
        "work_item_event_paperless_links",
        ["event_id"],
    )
    op.create_index(
        "ix_work_item_event_paperless_links_document_id",
        "work_item_event_paperless_links",
        ["document_id"],
    )
    op.create_index(
        "ix_work_item_event_paperless_links_created_at",
        "work_item_event_paperless_links",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_work_item_event_paperless_links_created_at",
        table_name="work_item_event_paperless_links",
    )
    op.drop_index(
        "ix_work_item_event_paperless_links_document_id",
        table_name="work_item_event_paperless_links",
    )
    op.drop_index(
        "ix_work_item_event_paperless_links_event_id",
        table_name="work_item_event_paperless_links",
    )
    op.drop_table("work_item_event_paperless_links")
    with op.batch_alter_table("work_items") as batch:
        batch.drop_constraint("ck_work_items_activity_kind", type_="check")
        batch.drop_index("ix_work_items_activity_kind")
        batch.drop_column("activity_kind")
    with op.batch_alter_table("work_subjects") as batch:
        batch.drop_column("profile_json")
