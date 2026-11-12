"""Ticket-based time tracking."""

import json

import sqlalchemy as sa
from alembic import op

revision = "0062"
down_revision = "0061"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_intervals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ticket", sa.String(100), nullable=False),
        sa.Column("customer", sa.String(200), nullable=False),
        sa.Column("info", sa.String(4000), nullable=False),
        sa.Column("started_at", sa.Float(), nullable=False),
        sa.Column("ended_at", sa.Float()),
        sa.Column("running", sa.Boolean(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_work_intervals_ticket", "work_intervals", ["ticket"])
    op.create_index(
        "uq_work_interval_running",
        "work_intervals",
        ["running"],
        unique=True,
        sqlite_where=sa.text("running = 1"),
    )

    connection = op.get_bind()
    for row in connection.execute(
        sa.text("SELECT id, enabled_modules_json, main_menu_modules_json FROM application_settings")
    ).mappings():
        values = {}
        for field in ("enabled_modules_json", "main_menu_modules_json"):
            modules = json.loads(row[field])
            if "time_tracking" not in modules:
                modules.append("time_tracking")
            values[field] = json.dumps(modules)
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
            field: json.dumps([m for m in json.loads(row[field]) if m != "time_tracking"])
            for field in ("enabled_modules_json", "main_menu_modules_json")
        }
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json=:enabled_modules_json, "
                "main_menu_modules_json=:main_menu_modules_json WHERE id=:id"
            ),
            {**values, "id": row["id"]},
        )
    op.drop_table("work_intervals")
