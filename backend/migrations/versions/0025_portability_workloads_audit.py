"""Add logical workloads and immutable audit history.

Revision ID: 0025
Revises: 0024
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_workloads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("host_asset_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("image_tag", sa.String(length=200), nullable=True),
        sa.Column("compose_project", sa.String(length=200), nullable=True),
        sa.Column("network_mode", sa.String(length=30), nullable=False),
        sa.Column("macvlan_address", sa.String(length=64), nullable=True),
        sa.Column("ports_json", sa.Text(), nullable=False),
        sa.Column("urls_json", sa.Text(), nullable=False),
        sa.Column("reverse_proxy", sa.String(length=500), nullable=True),
        sa.Column("dependencies_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["host_asset_id"], ["assets.id"]),
        sa.CheckConstraint(
            "network_mode IN ('bridge', 'host', 'macvlan', 'docker_network')",
            name="ck_service_workloads_network_mode",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'stopped', 'planned', 'unknown')",
            name="ck_service_workloads_status",
        ),
    )
    op.create_index(
        "ix_service_workloads_host_asset_id",
        "service_workloads",
        ["host_asset_id"],
    )
    op.create_index("ix_service_workloads_name", "service_workloads", ["name"])
    op.create_index("ix_service_workloads_status", "service_workloads", ["status"])
    op.create_index(
        "ix_service_workloads_network_mode",
        "service_workloads",
        ["network_mode"],
    )
    op.create_index("ix_service_workloads_deleted_at", "service_workloads", ["deleted_at"])
    op.create_index(
        "ix_service_workloads_compose_project",
        "service_workloads",
        ["compose_project"],
    )
    op.create_index(
        "uq_service_workloads_active_host_name",
        "service_workloads",
        ["host_asset_id", "name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("change_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_events_object_type", "audit_events", ["object_type"])
    op.create_index("ix_audit_events_object_id", "audit_events", ["object_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    op.create_index(
        "ix_audit_events_object",
        "audit_events",
        ["object_type", "object_id"],
    )
    op.create_index("ix_audit_events_created", "audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("service_workloads")
