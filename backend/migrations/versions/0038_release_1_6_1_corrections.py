"""Release 1.6.1 corrections and defaults.

Revision ID: 0038
Revises: 0037
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SMART_RELAY_TYPE_ID = "2d614a181d584bfd99fd3cf1fc3c21f1"
SHELLY_PRO_1_PRODUCT_ID = "b5a2101b0ed043f591f04a590a61a0d8"


def upgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        batch.add_column(
            sa.Column(
                "product_image_source_wikimedia_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch.add_column(
            sa.Column(
                "product_image_source_duckduckgo_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    with op.batch_alter_table("network_interfaces") as batch:
        batch.add_column(
            sa.Column(
                "is_primary",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.create_index(
            "uq_network_interfaces_active_primary_device",
            ["network_device_id"],
            unique=True,
            sqlite_where=sa.text("deleted_at IS NULL AND is_primary = 1"),
        )

    with op.batch_alter_table("home_assistant_asset_links") as batch:
        batch.drop_constraint("ck_home_assistant_asset_links_role", type_="check")
        batch.create_check_constraint(
            "ck_home_assistant_asset_links_role",
            "role IN ('primary_live', 'total_power', 'voltage', 'current', 'energy', "
            "'power_l1', 'power_l2', 'power_l3', 'voltage_l1', 'voltage_l2', "
            "'voltage_l3', 'switch_output', 'input', 'availability', 'diagnostic', "
            "'additional')",
        )

    op.drop_index(
        "uq_consumption_meters_active_primary_type",
        table_name="consumption_meters",
    )
    op.create_index(
        "uq_consumption_meters_active_primary_non_pv",
        "consumption_meters",
        ["meter_type"],
        unique=True,
        sqlite_where=sa.text(
            "deleted_at IS NULL AND primary_for_dashboard = 1 "
            "AND meter_type <> 'electricity_pv'"
        ),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT OR IGNORE INTO asset_types "
            "(id, name, code_prefix, description, icon, module_width, "
            "rated_current_a, contact_count, contact_type, created_at, updated_at) "
            "VALUES (:id, :name, :prefix, :description, :icon, 1, 16, 1, "
            "'normally_open', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ),
        {
            "id": SMART_RELAY_TYPE_ID,
            "name": "Smartes Relais / DIN-Schaltaktor",
            "prefix": "SRA",
            "icon": "mdi-electric-switch",
            "description": (
                "DIN-Schienen-Schaltaktor mit einem oder mehreren Kanälen; "
                "kein Stromstoßschalter. Netzwerk- und Home-Assistant-Zuordnungen "
                "werden am Asset dokumentiert."
            ),
        },
    )
    connection.execute(
        sa.text(
            "INSERT OR IGNORE INTO products "
            "(id, name, manufacturer, model_number, description, image_source, "
            "din_rail_mount, module_width, asset_type_id, created_at, updated_at) "
            "VALUES (:id, 'Shelly Pro 1', 'Shelly', 'Pro 1', :description, 'url', "
            "1, 1, :asset_type_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ),
        {
            "id": SHELLY_PRO_1_PRODUCT_ID,
            "asset_type_id": SMART_RELAY_TYPE_ID,
            "description": (
                "1-kanaliger DIN-Schaltaktor mit potentialfreiem Kontakt, LAN, "
                "WLAN und Bluetooth. Keine Leistungsmessung; dafür Shelly Pro 1PM verwenden."
            ),
        },
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM products WHERE id = :id"),
        {"id": SHELLY_PRO_1_PRODUCT_ID},
    )
    connection.execute(
        sa.text("DELETE FROM asset_types WHERE id = :id"),
        {"id": SMART_RELAY_TYPE_ID},
    )
    op.drop_index(
        "uq_consumption_meters_active_primary_non_pv",
        table_name="consumption_meters",
    )
    op.create_index(
        "uq_consumption_meters_active_primary_type",
        "consumption_meters",
        ["meter_type"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND primary_for_dashboard = 1"),
    )
    with op.batch_alter_table("home_assistant_asset_links") as batch:
        batch.drop_constraint("ck_home_assistant_asset_links_role", type_="check")
        batch.create_check_constraint(
            "ck_home_assistant_asset_links_role",
            "role IN ('primary_live', 'total_power', 'voltage', 'current', 'energy', "
            "'power_l1', 'power_l2', 'power_l3', 'voltage_l1', 'voltage_l2', "
            "'voltage_l3', 'additional')",
        )
    with op.batch_alter_table("network_interfaces") as batch:
        batch.drop_index("uq_network_interfaces_active_primary_device")
        batch.drop_column("is_primary")
    with op.batch_alter_table("application_settings") as batch:
        batch.drop_column("product_image_source_duckduckgo_enabled")
        batch.drop_column("product_image_source_wikimedia_enabled")
