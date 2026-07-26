"""Extend locations into the single-home spatial model.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-20
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LOCATION_TYPE_CONSTRAINT = (
    "location_type IN ('building', 'floor', 'room', 'area', 'cabinet', "
    "'installation_point', 'outdoor') AND "
    "((parent_id IS NULL AND location_type = 'building') OR "
    "(parent_id IS NOT NULL AND location_type <> 'building'))"
)


def _available_root_id(existing_ids: set[str]) -> UUID:
    sequence = 1
    while True:
        candidate = uuid5(NAMESPACE_URL, f"jarvis:spatial-root:{sequence}")
        if candidate.hex not in existing_ids:
            return candidate
        sequence += 1


def upgrade() -> None:
    connection = op.get_bind()
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")

    op.add_column("locations", sa.Column("location_type", sa.String(length=30), nullable=True))
    op.add_column("locations", sa.Column("short_name", sa.String(length=80), nullable=True))
    op.add_column("locations", sa.Column("sort_order", sa.Integer(), nullable=True))
    op.add_column("locations", sa.Column("notes", sa.String(), nullable=True))

    existing_ids = {
        str(row.id).replace("-", "")
        for row in connection.execute(sa.text("SELECT id FROM locations"))
    }
    root_id = _available_root_id(existing_ids)
    setting = connection.execute(
        sa.text(
            "SELECT installation_name, setup_completed_at "
            "FROM application_settings WHERE id = 1"
        )
    ).mappings().first()
    root_name = (
        str(setting["installation_name"])
        if setting is not None and setting["setup_completed_at"] is not None
        else "Home"
    )
    now = datetime.now(UTC)

    connection.execute(sa.text("UPDATE locations SET location_type = 'area'"))
    connection.execute(
        sa.text(
            "INSERT INTO locations "
            "(id, created_at, updated_at, deleted_at, name, location_type, description, "
            "parent_id, short_name, sort_order, notes) "
            "VALUES (:id, :created_at, :updated_at, NULL, :name, 'building', NULL, "
            "NULL, NULL, 0, NULL)"
        ),
        {
            "id": root_id.hex,
            "created_at": now,
            "updated_at": now,
            "name": root_name,
        },
    )
    connection.execute(
        sa.text(
            "UPDATE locations SET parent_id = :root_id "
            "WHERE id <> :root_id AND parent_id IS NULL"
        ),
        {"root_id": root_id.hex},
    )

    with op.batch_alter_table("locations") as batch_op:
        batch_op.alter_column(
            "location_type",
            existing_type=sa.String(length=30),
            nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_locations_type_and_hierarchy",
            LOCATION_TYPE_CONSTRAINT,
        )

    op.create_index("ix_locations_location_type", "locations", ["location_type"])
    op.create_index("ix_locations_short_name", "locations", ["short_name"])
    op.create_index("ix_locations_sort_order", "locations", ["sort_order"])
    op.create_index(
        "uq_locations_single_active_root",
        "locations",
        ["location_type"],
        unique=True,
        sqlite_where=sa.text("parent_id IS NULL AND deleted_at IS NULL"),
    )

    if sqlite:
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations after spatial migration: {violations}")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    connection = op.get_bind()
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")

    op.drop_index("uq_locations_single_active_root", table_name="locations")
    op.drop_index("ix_locations_sort_order", table_name="locations")
    op.drop_index("ix_locations_short_name", table_name="locations")
    op.drop_index("ix_locations_location_type", table_name="locations")
    with op.batch_alter_table("locations") as batch_op:
        batch_op.drop_constraint("ck_locations_type_and_hierarchy", type_="check")
        batch_op.drop_column("notes")
        batch_op.drop_column("sort_order")
        batch_op.drop_column("short_name")
        batch_op.drop_column("location_type")

    if sqlite:
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations after spatial downgrade: {violations}")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
