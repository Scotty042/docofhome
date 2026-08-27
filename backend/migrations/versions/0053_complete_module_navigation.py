"""Add images, documents and workloads to configurable module navigation.

Revision ID: 0053
Revises: 0052
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0053"
down_revision: str | None = "0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MODULES = ("images", "documents", "workloads")
COLUMNS = ("enabled_modules_json", "main_menu_modules_json")


def _update_modules(*, add: bool) -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, enabled_modules_json, main_menu_modules_json "
            "FROM application_settings"
        )
    ).mappings()
    for row in rows:
        updates: dict[str, str] = {}
        for column in COLUMNS:
            try:
                values = json.loads(row[column])
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(values, list):
                continue
            modules = [value for value in values if isinstance(value, str) and value not in MODULES]
            if add:
                modules.extend(MODULES)
            updates[column] = json.dumps(modules, separators=(",", ":"))
        if updates:
            assignments = ", ".join(f"{column} = :{column}" for column in updates)
            connection.execute(
                sa.text(f"UPDATE application_settings SET {assignments} WHERE id = :id"),
                {**updates, "id": row["id"]},
            )


def upgrade() -> None:
    # Diese drei Einträge waren bisher fest im Hauptmenü sichtbar. Beim Upgrade
    # bleiben sie daher für bestehende Installationen aktiviert und sichtbar.
    _update_modules(add=True)


def downgrade() -> None:
    _update_modules(add=False)
