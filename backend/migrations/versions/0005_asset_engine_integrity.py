"""Add immutable asset codes and Asset Engine integrity fields.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-20
"""

import re
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _prefix_for(name: str) -> str:
    words = re.findall(r"[A-Z0-9]+", name.upper())
    if not words:
        return "ASSET"
    if len(words) == 1:
        return words[0][:3]
    return f"{words[0][:2]}-{words[1][:4]}"


def _unique_value(base: str, used: set[str], *, max_length: int) -> str:
    candidate = base[:max_length]
    suffix = 2
    while candidate in used:
        marker = f"-{suffix}"
        candidate = f"{base[: max_length - len(marker)]}{marker}"
        suffix += 1
    used.add(candidate)
    return candidate


def _rows(connection: Any, query: str) -> list[dict[str, Any]]:
    result = connection.execute(sa.text(query))
    return [dict(row) for row in result.mappings()]


def upgrade() -> None:
    connection = op.get_bind()
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        # SQLite batch migrations recreate referenced tables. Runtime connections keep FK
        # enforcement enabled; this connection is checked and restored before the revision ends.
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")

    op.add_column("asset_types", sa.Column("code_prefix", sa.String(length=20), nullable=True))
    op.add_column("assets", sa.Column("jarvis_code", sa.String(length=32), nullable=True))
    op.add_column("labels", sa.Column("normalized_name", sa.String(length=100), nullable=True))
    op.create_table(
        "asset_code_counters",
        sa.Column("prefix", sa.String(length=20), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("prefix"),
    )

    used_prefixes: set[str] = set()
    types = _rows(connection, "SELECT id, name FROM asset_types ORDER BY created_at, id")
    prefix_by_type: dict[str, str] = {}
    for asset_type in types:
        prefix = _unique_value(_prefix_for(str(asset_type["name"])), used_prefixes, max_length=20)
        type_id = str(asset_type["id"])
        prefix_by_type[type_id] = prefix
        connection.execute(
            sa.text("UPDATE asset_types SET code_prefix = :prefix WHERE id = :id"),
            {"prefix": prefix, "id": asset_type["id"]},
        )

    next_by_prefix: dict[str, int] = {prefix: 1 for prefix in used_prefixes}
    assets = _rows(
        connection,
        "SELECT id, asset_type_id FROM assets ORDER BY asset_type_id, created_at, id",
    )
    for asset in assets:
        prefix = prefix_by_type[str(asset["asset_type_id"])]
        number = next_by_prefix[prefix]
        next_by_prefix[prefix] = number + 1
        connection.execute(
            sa.text("UPDATE assets SET jarvis_code = :code WHERE id = :id"),
            {"code": f"{prefix}-{number:03d}", "id": asset["id"]},
        )

    for prefix, next_value in next_by_prefix.items():
        connection.execute(
            sa.text(
                "INSERT INTO asset_code_counters (prefix, next_value) "
                "VALUES (:prefix, :next_value)"
            ),
            {"prefix": prefix, "next_value": next_value},
        )

    used_labels: set[str] = set()
    labels = _rows(connection, "SELECT id, name FROM labels ORDER BY created_at, id")
    for label in labels:
        base = str(label["name"]).strip().casefold() or f"label-{label['id']}"
        normalized = _unique_value(base, used_labels, max_length=100)
        connection.execute(
            sa.text("UPDATE labels SET normalized_name = :normalized WHERE id = :id"),
            {"normalized": normalized, "id": label["id"]},
        )

    with op.batch_alter_table("asset_types") as batch_op:
        batch_op.alter_column("code_prefix", existing_type=sa.String(length=20), nullable=False)
    with op.batch_alter_table("assets") as batch_op:
        batch_op.alter_column("jarvis_code", existing_type=sa.String(length=32), nullable=False)
    with op.batch_alter_table("labels") as batch_op:
        batch_op.alter_column(
            "normalized_name",
            existing_type=sa.String(length=100),
            nullable=False,
        )

    op.create_index("ix_asset_types_code_prefix", "asset_types", ["code_prefix"], unique=True)
    op.create_index("ix_assets_jarvis_code", "assets", ["jarvis_code"], unique=True)
    op.create_index("ix_labels_normalized_name", "labels", ["normalized_name"], unique=True)
    if sqlite:
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations after Asset Engine migration: {violations}")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    connection = op.get_bind()
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
    op.drop_index("ix_labels_normalized_name", table_name="labels")
    op.drop_index("ix_assets_jarvis_code", table_name="assets")
    op.drop_index("ix_asset_types_code_prefix", table_name="asset_types")
    with op.batch_alter_table("labels") as batch_op:
        batch_op.drop_column("normalized_name")
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_column("jarvis_code")
    with op.batch_alter_table("asset_types") as batch_op:
        batch_op.drop_column("code_prefix")
    op.drop_table("asset_code_counters")
    if sqlite:
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations after Asset Engine downgrade: {violations}")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
