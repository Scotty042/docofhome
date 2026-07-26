"""Remove the legacy one-source-per-target topology index.

Revision ID: 0033
Revises: 0032
Create Date: 2026-07-24

Older installations may already have marked migration 0027 as applied while
still retaining ``uq_electrical_connections_active_target``.  That index
prevents a cabinet component from receiving more than one active supply.  The
repair must therefore live in a new migration instead of relying on a changed
historical migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_INDEX = "uq_electrical_connections_active_target"


def _has_index(table_name: str, index_name: str) -> bool:
    return any(
        item.get("name") == index_name
        for item in sa.inspect(op.get_bind()).get_indexes(table_name)
    )


def upgrade() -> None:
    if _has_index("electrical_connections", LEGACY_INDEX):
        op.drop_index(LEGACY_INDEX, table_name="electrical_connections")


def downgrade() -> None:
    # Deliberately do not recreate the legacy unique target index.  Reintroducing
    # it could fail for valid multi-source topologies created after this repair
    # and would make a downgrade destructive or impossible.
    pass
