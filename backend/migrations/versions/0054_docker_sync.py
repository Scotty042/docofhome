"""Add Docker Engine synchronization metadata.

Revision ID: 0054
Revises: 0053
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0054"
down_revision: str | None = "0053"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("service_workloads") as batch:
        batch.add_column(sa.Column("docker_container_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("docker_status_text", sa.String(length=500), nullable=True))
        batch.add_column(sa.Column("docker_networks_json", sa.Text(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("docker_mounts_json", sa.Text(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("docker_last_seen_at", sa.DateTime(), nullable=True))
        batch.create_index("ix_service_workloads_docker_container_id", ["docker_container_id"], unique=False)
        batch.create_index("ix_service_workloads_docker_last_seen_at", ["docker_last_seen_at"], unique=False)

    op.create_table(
        "docker_sync_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("socket_path", sa.String(length=500), nullable=False, server_default="/var/run/docker.sock"),
        sa.Column("host_asset_id", sa.Uuid(), nullable=True),
        sa.Column("refresh_interval_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "refresh_interval_seconds IN (0, 30, 60, 300, 900, 1800)",
            name="ck_docker_sync_settings_interval",
        ),
        sa.ForeignKeyConstraint(["host_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_docker_sync_settings_host_asset_id", "docker_sync_settings", ["host_asset_id"])


def downgrade() -> None:
    op.drop_index("ix_docker_sync_settings_host_asset_id", table_name="docker_sync_settings")
    op.drop_table("docker_sync_settings")
    with op.batch_alter_table("service_workloads") as batch:
        batch.drop_index("ix_service_workloads_docker_last_seen_at")
        batch.drop_index("ix_service_workloads_docker_container_id")
        batch.drop_column("docker_last_seen_at")
        batch.drop_column("docker_mounts_json")
        batch.drop_column("docker_networks_json")
        batch.drop_column("docker_status_text")
        batch.drop_column("docker_container_id")
