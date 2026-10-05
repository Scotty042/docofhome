"""LEGO collection and configurable navigation."""

import json

import sqlalchemy as sa
from alembic import op

revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lego_sets",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("set_number", sa.String(30), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("theme", sa.String(100), nullable=False),
        sa.Column("release_year", sa.Integer()),
        sa.Column("parts_count", sa.Integer()),
        sa.Column("image_url", sa.String(1000)),
        sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id")),
        sa.Column("storage_note", sa.String(300), nullable=False),
        sa.Column("condition", sa.String(100), nullable=False),
        sa.Column("build_status", sa.String(20), nullable=False),
        sa.Column("complete", sa.Boolean()),
        sa.Column("box_present", sa.Boolean()),
        sa.Column("instructions_present", sa.Boolean()),
        sa.Column("purchase_date", sa.Date()),
        sa.Column("purchase_price", sa.Numeric(12, 2)),
        sa.Column("seller", sa.String(200), nullable=False),
        sa.Column("width_cm", sa.Float()),
        sa.Column("depth_cm", sa.Float()),
        sa.Column("height_cm", sa.Float()),
        sa.Column("dimensions_note", sa.String(500), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("researched_at", sa.Date()),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_lego_name"),
        sa.CheckConstraint("parts_count IS NULL OR parts_count >= 0", name="ck_lego_parts"),
        sa.CheckConstraint("purchase_price IS NULL OR purchase_price >= 0", name="ck_lego_price"),
        sa.CheckConstraint(
            "build_status IN ('built','disassembled','sealed')", name="ck_lego_status"
        ),
    )
    op.create_index("ix_lego_sets_set_number", "lego_sets", ["set_number"], unique=True)
    op.create_index("ix_lego_sets_name", "lego_sets", ["name"])
    op.create_index("ix_lego_sets_location_id", "lego_sets", ["location_id"])
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, enabled_modules_json, main_menu_modules_json FROM application_settings")
    ).mappings()
    for row in rows:
        updates = {}
        for field in ("enabled_modules_json", "main_menu_modules_json"):
            values = json.loads(row[field])
            if "lego" not in values:
                values.append("lego")
            updates[field] = json.dumps(values)
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json=:enabled_modules_json, "
                "main_menu_modules_json=:main_menu_modules_json WHERE id=:id"
            ),
            {**updates, "id": row["id"]},
        )


def downgrade():
    connection = op.get_bind()
    for row in connection.execute(
        sa.text("SELECT id, enabled_modules_json, main_menu_modules_json FROM application_settings")
    ).mappings():
        updates = {
            key: json.dumps([v for v in json.loads(row[key]) if v != "lego"])
            for key in ("enabled_modules_json", "main_menu_modules_json")
        }
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json=:enabled_modules_json, "
                "main_menu_modules_json=:main_menu_modules_json WHERE id=:id"
            ),
            {**updates, "id": row["id"]},
        )
    op.drop_table("lego_sets")
