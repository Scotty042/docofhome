"""Add multiple local or SSH Docker monitoring hosts."""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "docker_hosts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("connection_type", sa.String(length=20), nullable=False, server_default="ssh"),
        sa.Column("host_asset_id", sa.Uuid(), nullable=False),
        sa.Column("socket_path", sa.String(length=500), nullable=True),
        sa.Column("ssh_host", sa.String(length=255), nullable=True),
        sa.Column("ssh_port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("ssh_user", sa.String(length=100), nullable=True),
        sa.Column("ssh_host_key", sa.Text(), nullable=True),
        sa.Column("refresh_interval_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "connection_type IN ('socket', 'ssh')", name="ck_docker_hosts_connection_type"
        ),
        sa.CheckConstraint(
            "refresh_interval_seconds IN (0, 30, 60, 300, 900, 1800)",
            name="ck_docker_hosts_interval",
        ),
        sa.ForeignKeyConstraint(["host_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_docker_hosts_host_asset_id", "docker_hosts", ["host_asset_id"])
    op.create_index("uq_docker_hosts_asset", "docker_hosts", ["host_asset_id"], unique=True)

    connection = op.get_bind()
    legacy = (
        connection.execute(sa.text("SELECT * FROM docker_sync_settings WHERE id = 1"))
        .mappings()
        .first()
    )
    if legacy and legacy["host_asset_id"]:
        now = sa.func.current_timestamp()
        connection.execute(
            sa.insert(
                sa.table(
                    "docker_hosts",
                    sa.column("id"),
                    sa.column("name"),
                    sa.column("enabled"),
                    sa.column("connection_type"),
                    sa.column("host_asset_id"),
                    sa.column("socket_path"),
                    sa.column("ssh_port"),
                    sa.column("refresh_interval_seconds"),
                    sa.column("last_attempt_at"),
                    sa.column("last_success_at"),
                    sa.column("last_error"),
                    sa.column("created_at"),
                    sa.column("updated_at"),
                )
            ).values(
                id=uuid4().hex,
                name="Lokaler Docker-Host",
                enabled=legacy["enabled"],
                connection_type="socket",
                host_asset_id=legacy["host_asset_id"],
                socket_path=legacy["socket_path"],
                ssh_port=22,
                refresh_interval_seconds=legacy["refresh_interval_seconds"],
                last_attempt_at=legacy["last_attempt_at"],
                last_success_at=legacy["last_success_at"],
                last_error=legacy["last_error"],
                created_at=now,
                updated_at=now,
            )
        )


def downgrade() -> None:
    op.drop_index("uq_docker_hosts_asset", table_name="docker_hosts")
    op.drop_index("ix_docker_hosts_host_asset_id", table_name="docker_hosts")
    op.drop_table("docker_hosts")
