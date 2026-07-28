"""Release 1.7.1 data integrity, asset images and IP reconciliation.

Revision ID: 0048
Revises: 0047
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: str | None = "0047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("asset_types") as batch:
        batch.add_column(sa.Column("image_url", sa.String(length=1000), nullable=True))
        batch.add_column(
            sa.Column("image_source", sa.String(length=20), nullable=False, server_default="url")
        )
        batch.add_column(sa.Column("image_reference", sa.String(length=1000), nullable=True))
        batch.add_column(
            sa.Column("is_meter", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column(
                "switch_port_layout",
                sa.String(length=30),
                nullable=False,
                server_default="odd_even",
            )
        )
        batch.create_check_constraint(
            "ck_asset_types_image_source",
            "image_source IN ('url', 'upload', 'immich', 'online')",
        )
        batch.create_check_constraint(
            "ck_asset_types_switch_port_layout",
            "switch_port_layout IN ('odd_even', 'sequential_halves')",
        )
    op.create_index("ix_asset_types_is_meter", "asset_types", ["is_meter"])
    op.execute(sa.text("""
        UPDATE asset_types
        SET is_meter=1
        WHERE lower(name) LIKE '%zähler%'
           OR lower(name) LIKE '%zaehler%'
           OR lower(name) LIKE '%meter%'
    """))

    with op.batch_alter_table("assets") as batch:
        batch.add_column(sa.Column("image_url", sa.String(length=1000), nullable=True))
        batch.add_column(
            sa.Column("image_source", sa.String(length=20), nullable=False, server_default="url")
        )
        batch.add_column(sa.Column("image_reference", sa.String(length=1000), nullable=True))
        batch.create_check_constraint(
            "ck_assets_image_source",
            "image_source IN ('url', 'upload', 'immich', 'online')",
        )

    with op.batch_alter_table("electrical_circuits") as batch:
        batch.add_column(sa.Column("protective_device_asset_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_electrical_circuits_protective_device_asset",
            "assets",
            ["protective_device_asset_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_electrical_circuits_single_protective_reference",
            "protective_device_id IS NULL OR protective_device_asset_id IS NULL",
        )
    op.create_index(
        "ix_electrical_circuits_protective_device_asset_id",
        "electrical_circuits",
        ["protective_device_asset_id"],
    )

    with op.batch_alter_table("network_interfaces") as batch:
        batch.drop_constraint("ck_network_interfaces_speed", type_="check")
        batch.create_check_constraint(
            "ck_network_interfaces_speed",
            "speed_mbps IS NULL OR speed_mbps IN (100, 1000, 2500)",
        )

    with op.batch_alter_table("electrical_connections") as batch:
        batch.add_column(
            sa.Column("phase_source", sa.String(length=20), nullable=False, server_default="manual")
        )
        batch.add_column(sa.Column("source_connection_id", sa.Uuid(), nullable=True))
        batch.create_check_constraint(
            "ck_electrical_connections_phase_source",
            "phase_source IN ('manual', 'wire', 'busbar')",
        )
    op.create_index(
        "ix_electrical_connections_phase_source",
        "electrical_connections",
        ["phase_source"],
    )
    op.create_index(
        "ix_electrical_connections_source_connection_id",
        "electrical_connections",
        ["source_connection_id"],
    )
    op.execute(sa.text("""
        UPDATE electrical_connections
        SET phase_source='wire', source_connection_id=id
        WHERE deleted_at IS NULL AND connection_type IN ('wire', 'cable')
    """))
    op.execute(sa.text("""
        UPDATE electrical_connections
        SET phase_source='busbar', source_connection_id=id
        WHERE deleted_at IS NULL
          AND connection_type='busbar'
          AND source_kind='cabinet_component'
          AND EXISTS (
              SELECT 1
              FROM electrical_cabinet_components component
              WHERE component.id=electrical_connections.source_id
                AND component.deleted_at IS NULL
                AND component.component_type='phase_rail'
          )
    """))

    op.create_table(
        "network_observed_addresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interface_id", sa.Uuid(), nullable=True),
        sa.Column("mac_address", sa.String(length=17), nullable=True),
        sa.Column("address", sa.String(length=64), nullable=False),
        sa.Column("hostname", sa.String(length=253), nullable=True),
        sa.Column("assignment_type", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("ignored", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "assignment_type IN ('static', 'dhcp', 'reservation', 'link_local', 'unknown')",
            name="ck_network_observed_addresses_assignment_type",
        ),
        sa.ForeignKeyConstraint(["interface_id"], ["network_interfaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_network_observed_addresses_deleted_at", ["deleted_at"]),
        ("ix_network_observed_addresses_interface_id", ["interface_id"]),
        ("ix_network_observed_addresses_mac_address", ["mac_address"]),
        ("ix_network_observed_addresses_address", ["address"]),
        ("ix_network_observed_addresses_hostname", ["hostname"]),
        ("ix_network_observed_addresses_assignment_type", ["assignment_type"]),
        ("ix_network_observed_addresses_source", ["source"]),
        ("ix_network_observed_addresses_active", ["active"]),
        ("ix_network_observed_addresses_ignored", ["ignored"]),
        ("ix_network_observed_addresses_last_seen_at", ["last_seen_at"]),
        ("ix_network_observed_source_mac", ["source", "mac_address"]),
        ("ix_network_observed_address", ["address"]),
    ):
        op.create_index(name, "network_observed_addresses", columns)

    op.create_table(
        "network_address_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_address_id", sa.Uuid(), nullable=False),
        sa.Column("documented_address_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("old_address", sa.String(length=64), nullable=True),
        sa.Column("new_address", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["observed_address_id"], ["network_observed_addresses.id"]
        ),
        sa.ForeignKeyConstraint(["documented_address_id"], ["network_addresses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_network_address_changes_deleted_at", ["deleted_at"]),
        ("ix_network_address_changes_observed_address_id", ["observed_address_id"]),
        ("ix_network_address_changes_documented_address_id", ["documented_address_id"]),
    ):
        op.create_index(name, "network_address_changes", columns)


def downgrade() -> None:
    op.drop_table("network_address_changes")
    op.drop_table("network_observed_addresses")

    op.drop_index(
        "ix_electrical_circuits_protective_device_asset_id",
        table_name="electrical_circuits",
    )
    with op.batch_alter_table("electrical_circuits") as batch:
        batch.drop_constraint(
            "ck_electrical_circuits_single_protective_reference", type_="check"
        )
        batch.drop_constraint(
            "fk_electrical_circuits_protective_device_asset", type_="foreignkey"
        )
        batch.drop_column("protective_device_asset_id")

    op.drop_index(
        "ix_electrical_connections_source_connection_id",
        table_name="electrical_connections",
    )
    op.drop_index(
        "ix_electrical_connections_phase_source",
        table_name="electrical_connections",
    )
    with op.batch_alter_table("electrical_connections") as batch:
        batch.drop_constraint("ck_electrical_connections_phase_source", type_="check")
        batch.drop_column("source_connection_id")
        batch.drop_column("phase_source")

    with op.batch_alter_table("network_interfaces") as batch:
        batch.drop_constraint("ck_network_interfaces_speed", type_="check")
        batch.create_check_constraint(
            "ck_network_interfaces_speed",
            "speed_mbps IS NULL OR (speed_mbps >= 1 AND speed_mbps <= 1000000)",
        )

    with op.batch_alter_table("assets") as batch:
        batch.drop_constraint("ck_assets_image_source", type_="check")
        batch.drop_column("image_reference")
        batch.drop_column("image_source")
        batch.drop_column("image_url")

    op.drop_index("ix_asset_types_is_meter", table_name="asset_types")
    with op.batch_alter_table("asset_types") as batch:
        batch.drop_constraint("ck_asset_types_switch_port_layout", type_="check")
        batch.drop_constraint("ck_asset_types_image_source", type_="check")
        batch.drop_column("switch_port_layout")
        batch.drop_column("is_meter")
        batch.drop_column("image_reference")
        batch.drop_column("image_source")
        batch.drop_column("image_url")
