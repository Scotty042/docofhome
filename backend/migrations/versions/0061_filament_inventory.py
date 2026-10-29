"""Filament inventory, persistent cloud identity, and observed AMS slots."""

import json

import sqlalchemy as sa
from alembic import op

revision = "0061"
down_revision = "0060"
branch_labels = None
depends_on = None


def upgrade():
    columns = [
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("label_code", sa.String(40), nullable=False),
    ]
    for name, size in {
        "manufacturer": 100,
        "material": 100,
        "variant": 200,
        "color_name": 200,
        "color_hex": 9,
        "shop_code": 100,
        "condition": 20,
        "storage_note": 300,
        "reorder_note": 1000,
        "cloud_product_code": 100,
    }.items():
        columns.append(sa.Column(name, sa.String(size), nullable=False))
    for name, size in {
        "image_url": 1000,
        "image_source_url": 1000,
        "cloud_account": 64,
        "cloud_id": 100,
        "rfid": 100,
        "printer_serial": 100,
        "ams_id": 100,
        "slot_id": 100,
        "mount_source": 20,
    }.items():
        columns.append(sa.Column(name, sa.String(size)))
    for name in ("initial_g", "remaining_g", "remaining_percent"):
        columns.append(sa.Column(name, sa.Float()))
    for name in ("cloud_sync_at", "mount_observed_at", "last_seen_at", "archived_at"):
        columns.append(sa.Column(name, sa.DateTime()))
    columns.extend(
        [
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("reorder", sa.Boolean(), nullable=False),
            sa.Column("image_verified", sa.Boolean(), nullable=False),
            sa.Column("cloud_present", sa.Boolean()),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id")),
            sa.UniqueConstraint("cloud_account", "cloud_id", name="uq_filament_cloud_identity"),
            sa.CheckConstraint("condition IN ('sealed','open')", name="ck_filament_condition"),
            sa.CheckConstraint(
                "remaining_g IS NULL OR remaining_g >= 0", name="ck_filament_remaining"
            ),
        ]
    )
    op.create_table("filament_spools", *columns)
    for name in ("label_code", "material", "rfid", "location_id", "archived_at"):
        op.create_index(
            f"ix_filament_spools_{name}", "filament_spools", [name], unique=name == "label_code"
        )
    op.create_table(
        "filament_slots",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("printer_serial", sa.String(100), nullable=False),
        sa.Column("ams_id", sa.String(100), nullable=False),
        sa.Column("slot_id", sa.String(100), nullable=False),
        sa.Column("spool_id", sa.Uuid(), sa.ForeignKey("filament_spools.id")),
        sa.Column("rfid", sa.String(100)),
        sa.Column("tag_uid", sa.String(100)),
        sa.Column("material", sa.String(100), nullable=False),
        sa.Column("color_hex", sa.String(9), nullable=False),
        sa.Column("remaining_percent", sa.Float()),
        sa.Column("occupied", sa.Boolean(), nullable=False),
        sa.Column("manual_binding", sa.Boolean(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("printer_serial", "ams_id", "slot_id", name="uq_filament_slot"),
    )
    connection = op.get_bind()
    for row in connection.execute(
        sa.text("SELECT id, enabled_modules_json, main_menu_modules_json FROM application_settings")
    ).mappings():
        values = {
            key: json.dumps(list(dict.fromkeys([*json.loads(row[key]), "filament"])))
            for key in ("enabled_modules_json", "main_menu_modules_json")
        }
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json=:enabled_modules_json, "
                "main_menu_modules_json=:main_menu_modules_json WHERE id=:id"
            ),
            {**values, "id": row["id"]},
        )


def downgrade():
    connection = op.get_bind()
    for row in connection.execute(
        sa.text("SELECT id, enabled_modules_json, main_menu_modules_json FROM application_settings")
    ).mappings():
        values = {
            key: json.dumps([v for v in json.loads(row[key]) if v != "filament"])
            for key in ("enabled_modules_json", "main_menu_modules_json")
        }
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json=:enabled_modules_json, "
                "main_menu_modules_json=:main_menu_modules_json WHERE id=:id"
            ),
            {**values, "id": row["id"]},
        )
    op.drop_table("filament_slots")
    op.drop_table("filament_spools")
