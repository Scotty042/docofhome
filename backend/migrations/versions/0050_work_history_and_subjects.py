"""Add reusable work subjects and detailed activity history.

Revision ID: 0050
Revises: 0049
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: str | None = "0049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "work_subjects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("subject_type", sa.String(length=30), nullable=False, server_default="general"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "subject_type IN ('device', 'animal', 'vehicle', 'building', 'room', "
            "'installation', 'general', 'other')",
            name="ck_work_subjects_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_subjects_name", "work_subjects", ["name"])
    op.create_index("ix_work_subjects_subject_type", "work_subjects", ["subject_type"])
    op.create_index("ix_work_subjects_deleted_at", "work_subjects", ["deleted_at"])
    op.create_index(
        "uq_work_subjects_active_name_type",
        "work_subjects",
        ["name", "subject_type"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    with op.batch_alter_table("work_items") as batch:
        batch.add_column(sa.Column("subject_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_work_items_subject_id",
            "work_subjects",
            ["subject_id"],
            ["id"],
        )
    op.create_index("ix_work_items_subject_id", "work_items", ["subject_id"])

    with op.batch_alter_table("work_item_events") as batch:
        batch.add_column(sa.Column("occurred_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("cost_amount", sa.Float(), nullable=True))
        batch.add_column(sa.Column("cost_currency", sa.String(length=3), nullable=True))
        batch.add_column(sa.Column("reading_value", sa.Float(), nullable=True))
        batch.add_column(sa.Column("reading_unit", sa.String(length=30), nullable=True))
        batch.create_check_constraint(
            "ck_work_item_events_cost_amount",
            "cost_amount IS NULL OR cost_amount >= 0",
        )
    op.execute(sa.text("UPDATE work_item_events SET occurred_at = created_at WHERE occurred_at IS NULL"))
    with op.batch_alter_table("work_item_events") as batch:
        batch.alter_column("occurred_at", existing_type=sa.DateTime(), nullable=False)
    op.create_index("ix_work_item_events_occurred_at", "work_item_events", ["occurred_at"])

    op.create_table(
        "work_item_event_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["work_item_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_item_event_attachments_event_id",
        "work_item_event_attachments",
        ["event_id"],
    )
    op.create_index(
        "ix_work_item_event_attachments_created_at",
        "work_item_event_attachments",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_work_item_event_attachments_created_at",
        table_name="work_item_event_attachments",
    )
    op.drop_index(
        "ix_work_item_event_attachments_event_id",
        table_name="work_item_event_attachments",
    )
    op.drop_table("work_item_event_attachments")

    op.drop_index("ix_work_item_events_occurred_at", table_name="work_item_events")
    with op.batch_alter_table("work_item_events") as batch:
        batch.drop_constraint("ck_work_item_events_cost_amount", type_="check")
        batch.drop_column("reading_unit")
        batch.drop_column("reading_value")
        batch.drop_column("cost_currency")
        batch.drop_column("cost_amount")
        batch.drop_column("occurred_at")

    op.drop_index("ix_work_items_subject_id", table_name="work_items")
    with op.batch_alter_table("work_items") as batch:
        batch.drop_constraint("fk_work_items_subject_id", type_="foreignkey")
        batch.drop_column("subject_id")

    op.drop_index("uq_work_subjects_active_name_type", table_name="work_subjects")
    op.drop_index("ix_work_subjects_deleted_at", table_name="work_subjects")
    op.drop_index("ix_work_subjects_subject_type", table_name="work_subjects")
    op.drop_index("ix_work_subjects_name", table_name="work_subjects")
    op.drop_table("work_subjects")
