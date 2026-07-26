"""Create directed electrical supply connections.

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "electrical_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("target_kind", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("connection_type", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=True),
        sa.Column("phase_l1", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("phase_l2", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("phase_l3", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("neutral", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "protective_earth",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("cable_type", sa.String(length=150), nullable=True),
        sa.Column("cores", sa.Integer(), nullable=True),
        sa.Column("cross_section_mm2", sa.Float(), nullable=True),
        sa.Column("length_m", sa.Float(), nullable=True),
        sa.Column("route", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "source_kind IN ('asset', 'distribution', 'protective_device', 'circuit')",
            name="ck_electrical_connections_source_kind",
        ),
        sa.CheckConstraint(
            "target_kind IN ('asset', 'distribution', 'protective_device', 'circuit')",
            name="ck_electrical_connections_target_kind",
        ),
        sa.CheckConstraint(
            "connection_type IN ('unknown', 'cable', 'wire', 'busbar', 'internal')",
            name="ck_electrical_connections_type",
        ),
        sa.CheckConstraint(
            "source_kind <> target_kind OR source_id <> target_id",
            name="ck_electrical_connections_distinct_endpoints",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "source_kind",
        "source_id",
        "target_kind",
        "target_id",
        "connection_type",
        "deleted_at",
    ):
        op.create_index(
            f"ix_electrical_connections_{column}",
            "electrical_connections",
            [column],
        )
    op.create_index(
        "uq_electrical_connections_active_pair",
        "electrical_connections",
        ["source_kind", "source_id", "target_kind", "target_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_electrical_connections_active_target",
        "electrical_connections",
        ["target_kind", "target_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_electrical_connections_active_target",
        table_name="electrical_connections",
    )
    op.drop_index(
        "uq_electrical_connections_active_pair",
        table_name="electrical_connections",
    )
    for column in reversed(
        (
            "source_kind",
            "source_id",
            "target_kind",
            "target_id",
            "connection_type",
            "deleted_at",
        )
    ):
        op.drop_index(
            f"ix_electrical_connections_{column}",
            table_name="electrical_connections",
        )
    op.drop_table("electrical_connections")
