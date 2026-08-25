"""Add local Home Assistant entity visibility selection.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "home_assistant_selection_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "id = 1",
            name="ck_home_assistant_selection_settings_singleton",
        ),
        sa.CheckConstraint(
            "mode IN ('all', 'selected')",
            name="ck_home_assistant_selection_settings_mode",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "home_assistant_entity_selections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("setting_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "setting_id = 1",
            name="ck_home_assistant_entity_selections_singleton",
        ),
        sa.CheckConstraint(
            "length(trim(entity_id)) BETWEEN 3 AND 255 AND instr(entity_id, '.') > 1",
            name="ck_home_assistant_entity_selections_entity_id",
        ),
        sa.ForeignKeyConstraint(
            ["setting_id"],
            ["home_assistant_selection_settings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "entity_id",
            name="uq_home_assistant_entity_selections_entity_id",
        ),
    )
    op.create_index(
        "ix_home_assistant_entity_selections_entity_id",
        "home_assistant_entity_selections",
        ["entity_id"],
    )


def downgrade() -> None:
    op.drop_table("home_assistant_entity_selections")
    op.drop_table("home_assistant_selection_settings")
