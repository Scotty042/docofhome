"""Create tasks, recurring maintenance plans, and completion history.

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-22
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _update_module(module: str, *, add: bool) -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, enabled_modules_json FROM application_settings")
    ).mappings()
    for row in rows:
        try:
            modules = json.loads(row["enabled_modules_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(modules, list):
            continue
        modules = [value for value in modules if isinstance(value, str) and value != module]
        if add:
            modules.append(module)
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json = :modules WHERE id = :id"
            ),
            {"modules": json.dumps(modules, separators=(",", ":")), "id": row["id"]},
        )


def upgrade() -> None:
    op.create_table(
        "work_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_type", sa.String(length=30), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("recurrence_days", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("item_type IN ('task', 'maintenance')", name="ck_work_items_item_type"),
        sa.CheckConstraint(
            "status IN ('open', 'completed', 'cancelled')",
            name="ck_work_items_status",
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'normal', 'high')",
            name="ck_work_items_priority",
        ),
        sa.CheckConstraint(
            "target_type IS NULL OR target_type IN ('asset', 'location', 'distribution', "
            "'protective_device', 'circuit')",
            name="ck_work_items_target_type",
        ),
        sa.CheckConstraint(
            "(target_type IS NULL AND target_id IS NULL) OR "
            "(target_type IS NOT NULL AND target_id IS NOT NULL)",
            name="ck_work_items_target_pair",
        ),
        sa.CheckConstraint(
            "recurrence_days IS NULL OR (recurrence_days >= 1 AND recurrence_days <= 3650)",
            name="ck_work_items_recurrence_days",
        ),
        sa.CheckConstraint(
            "recurrence_days IS NULL OR item_type = 'maintenance'",
            name="ck_work_items_recurrence_type",
        ),
        sa.CheckConstraint(
            "recurrence_days IS NULL OR due_at IS NOT NULL",
            name="ck_work_items_recurrence_due",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "item_type",
        "title",
        "target_type",
        "target_id",
        "due_at",
        "priority",
        "status",
        "deleted_at",
    ):
        op.create_index(f"ix_work_items_{column}", "work_items", [column])
    op.create_index(
        "ix_work_items_open_due",
        "work_items",
        ["status", "due_at"],
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "work_item_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_item_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("due_at_before", sa.DateTime(), nullable=True),
        sa.Column("due_at_after", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('completed', 'reopened', 'cancelled')",
            name="ck_work_item_events_type",
        ),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_item_events_work_item_id", "work_item_events", ["work_item_id"])
    op.create_index("ix_work_item_events_event_type", "work_item_events", ["event_type"])
    op.create_index("ix_work_item_events_created_at", "work_item_events", ["created_at"])
    _update_module("maintenance", add=True)


def downgrade() -> None:
    _update_module("maintenance", add=False)
    op.drop_index("ix_work_item_events_created_at", table_name="work_item_events")
    op.drop_index("ix_work_item_events_event_type", table_name="work_item_events")
    op.drop_index("ix_work_item_events_work_item_id", table_name="work_item_events")
    op.drop_table("work_item_events")
    op.drop_index("ix_work_items_open_due", table_name="work_items")
    for column in reversed(
        (
            "item_type",
            "title",
            "target_type",
            "target_id",
            "due_at",
            "priority",
            "status",
            "deleted_at",
        )
    ):
        op.drop_index(f"ix_work_items_{column}", table_name="work_items")
    op.drop_table("work_items")
