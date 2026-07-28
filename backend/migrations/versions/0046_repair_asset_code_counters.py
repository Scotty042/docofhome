"""Repair missing or stale asset code counters.

Revision ID: 0046
Revises: 0045
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _number_for(prefix: str, code: object | None) -> int | None:
    if code is None:
        return None
    value = str(code)
    marker = f"{prefix}-"
    if not value.startswith(marker):
        return None
    suffix = value[len(marker):]
    return int(suffix) if suffix.isdigit() else None


def upgrade() -> None:
    connection = op.get_bind()
    prefixes = [
        str(row["code_prefix"])
        for row in connection.execute(sa.text(
            "SELECT code_prefix FROM asset_types WHERE code_prefix IS NOT NULL"
        )).mappings()
    ]
    codes = [
        row["jarvis_code"]
        for row in connection.execute(sa.text(
            "SELECT jarvis_code FROM assets WHERE jarvis_code IS NOT NULL"
        )).mappings()
    ]

    for prefix in prefixes:
        highest = max(
            (number for code in codes if (number := _number_for(prefix, code)) is not None),
            default=0,
        )
        required_next = highest + 1
        current = connection.execute(
            sa.text(
                "SELECT next_value FROM asset_code_counters WHERE prefix=:prefix"
            ),
            {"prefix": prefix},
        ).scalar_one_or_none()
        if current is None:
            connection.execute(
                sa.text(
                    "INSERT INTO asset_code_counters (prefix, next_value) "
                    "VALUES (:prefix, :next_value)"
                ),
                {"prefix": prefix, "next_value": required_next},
            )
        elif int(current) < required_next:
            connection.execute(
                sa.text(
                    "UPDATE asset_code_counters SET next_value=:next_value "
                    "WHERE prefix=:prefix"
                ),
                {"prefix": prefix, "next_value": required_next},
            )


def downgrade() -> None:
    # Integrity repair only. Removing reconstructed counters would make existing
    # asset types unable to allocate stable DocOfHome codes again.
    pass
