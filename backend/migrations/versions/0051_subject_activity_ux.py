"""Make subject activities date based and independent from a seed due date.

Revision ID: 0051
Revises: 0050
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0051"
down_revision: str | None = "0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1.7.4.9 accepted a two-digit year from datetime-local controls. Repair
    # those rows before interval calculations and ordering use them.
    op.execute(sa.text("""
        UPDATE work_item_events
        SET occurred_at = datetime(occurred_at, '+2000 years')
        WHERE occurred_at IS NOT NULL
          AND CAST(substr(occurred_at, 1, 4) AS INTEGER) BETWEEN 0 AND 99
    """))
    op.execute(sa.text("""
        UPDATE work_items
        SET due_at = datetime(due_at, '+2000 years')
        WHERE due_at IS NOT NULL
          AND CAST(substr(due_at, 1, 4) AS INTEGER) BETWEEN 0 AND 99
    """))
    with op.batch_alter_table("work_items") as batch:
        batch.drop_constraint("ck_work_items_recurrence_due", type_="check")
        batch.drop_constraint("ck_work_items_calendar_months", type_="check")
        batch.create_check_constraint(
            "ck_work_items_calendar_months",
            "calendar_months IS NULL OR (calendar_months >= 1 AND calendar_months <= 120)",
        )


def downgrade() -> None:
    # Data entered without a seed due date remains valid history. A downgrade
    # therefore keeps the relaxed recurrence constraints to avoid data loss.
    pass
