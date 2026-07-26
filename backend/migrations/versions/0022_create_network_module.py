"""Create the local network documentation module.

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-22
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
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
        "network_devices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("hostname", sa.String(length=253), nullable=True),
        sa.Column("management_url", sa.String(length=1000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "role IN ('router', 'firewall', 'switch', 'access_point', 'server', "
            "'nas', 'client', 'iot', 'printer', 'controller', 'other')",
            name="ck_network_devices_role",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_network_devices_deleted_at", "network_devices", ["deleted_at"])
    op.create_index("ix_network_devices_asset_id", "network_devices", ["asset_id"])
    op.create_index("ix_network_devices_role", "network_devices", ["role"])
    op.create_index("ix_network_devices_hostname", "network_devices", ["hostname"])
    op.create_index(
        "uq_network_devices_active_asset",
        "network_devices",
        ["asset_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "network_segments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("cidr", sa.String(length=64), nullable=False),
        sa.Column("vlan_id", sa.Integer(), nullable=True),
        sa.Column("gateway", sa.String(length=64), nullable=True),
        sa.Column("dns_servers_json", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "vlan_id IS NULL OR (vlan_id >= 1 AND vlan_id <= 4094)",
            name="ck_network_segments_vlan_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "name", "cidr", "vlan_id"):
        op.create_index(f"ix_network_segments_{column}", "network_segments", [column])
    op.create_index(
        "uq_network_segments_active_name",
        "network_segments",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_network_segments_active_vlan",
        "network_segments",
        ["vlan_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND vlan_id IS NOT NULL"),
    )

    op.create_table(
        "network_interfaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("network_device_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("interface_type", sa.String(length=20), nullable=False),
        sa.Column("mac_address", sa.String(length=17), nullable=True),
        sa.Column("speed_mbps", sa.Integer(), nullable=True),
        sa.Column("poe_mode", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "interface_type IN ('ethernet', 'wifi', 'fiber', 'virtual', 'cellular', 'other')",
            name="ck_network_interfaces_type",
        ),
        sa.CheckConstraint(
            "poe_mode IN ('none', 'source', 'sink', 'passive', 'unknown')",
            name="ck_network_interfaces_poe_mode",
        ),
        sa.CheckConstraint(
            "speed_mbps IS NULL OR speed_mbps > 0",
            name="ck_network_interfaces_speed",
        ),
        sa.ForeignKeyConstraint(["network_device_id"], ["network_devices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "network_device_id", "name", "interface_type", "mac_address", "enabled"):
        op.create_index(f"ix_network_interfaces_{column}", "network_interfaces", [column])
    op.create_index(
        "uq_network_interfaces_active_name",
        "network_interfaces",
        ["network_device_id", "name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_network_interfaces_active_mac",
        "network_interfaces",
        ["mac_address"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND mac_address IS NOT NULL"),
    )

    op.create_table(
        "network_addresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("interface_id", sa.Uuid(), nullable=False),
        sa.Column("segment_id", sa.Uuid(), nullable=True),
        sa.Column("address", sa.String(length=64), nullable=False),
        sa.Column("assignment_type", sa.String(length=20), nullable=False),
        sa.Column("hostname", sa.String(length=253), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "assignment_type IN ('static', 'dhcp', 'reservation', 'link_local', 'unknown')",
            name="ck_network_addresses_assignment_type",
        ),
        sa.ForeignKeyConstraint(["interface_id"], ["network_interfaces.id"]),
        sa.ForeignKeyConstraint(["segment_id"], ["network_segments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "interface_id", "segment_id", "address", "assignment_type", "hostname", "is_primary"):
        op.create_index(f"ix_network_addresses_{column}", "network_addresses", [column])
    op.create_index(
        "uq_network_addresses_active_interface_address",
        "network_addresses",
        ["interface_id", "address"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_network_addresses_active_segment_address",
        "network_addresses",
        ["segment_id", "address"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND segment_id IS NOT NULL"),
    )

    op.create_table(
        "network_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("source_interface_id", sa.Uuid(), nullable=False),
        sa.Column("target_interface_id", sa.Uuid(), nullable=False),
        sa.Column("connection_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cable_type", sa.String(length=100), nullable=True),
        sa.Column("cable_label", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "source_interface_id <> target_interface_id",
            name="ck_network_connections_distinct_endpoints",
        ),
        sa.CheckConstraint(
            "connection_type IN ('physical', 'logical', 'wireless')",
            name="ck_network_connections_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'planned', 'inactive')",
            name="ck_network_connections_status",
        ),
        sa.ForeignKeyConstraint(["source_interface_id"], ["network_interfaces.id"]),
        sa.ForeignKeyConstraint(["target_interface_id"], ["network_interfaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("deleted_at", "source_interface_id", "target_interface_id", "connection_type", "status", "cable_label"):
        op.create_index(f"ix_network_connections_{column}", "network_connections", [column])
    op.create_index(
        "uq_network_connections_active_endpoints",
        "network_connections",
        ["source_interface_id", "target_interface_id"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    _update_module("network", add=True)


def downgrade() -> None:
    _update_module("network", add=False)
    op.drop_table("network_connections")
    op.drop_table("network_addresses")
    op.drop_table("network_interfaces")
    op.drop_table("network_segments")
    op.drop_table("network_devices")
