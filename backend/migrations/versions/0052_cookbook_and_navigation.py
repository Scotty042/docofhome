"""Add cookbook recipes and separate main-menu visibility.

Revision ID: 0052
Revises: 0051
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0052"
down_revision: str | None = "0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    with op.batch_alter_table("application_settings") as batch:
        batch.add_column(sa.Column("main_menu_modules_json", sa.String(), nullable=False,
            server_default='["locations","electrical","assets","master_data","network","smart_home","consumption","wiki","maintenance","quality"]'))
    op.create_table("recipes",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False), sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("preparation_minutes", sa.Integer()), sa.Column("cooking_minutes", sa.Integer()),
        sa.Column("servings", sa.Float(), nullable=False), sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("image_url", sa.String(1000)), sa.Column("ingredients_json", sa.Text(), nullable=False),
        sa.Column("steps_json", sa.Text(), nullable=False), sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(1000)), sa.Column("attachments_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_recipes_title", "recipes", ["title"]); op.create_index("ix_recipes_category", "recipes", ["category"])
    op.create_index("ix_recipes_favorite", "recipes", ["favorite"]); op.create_index("ix_recipes_updated_at", "recipes", ["updated_at"])

def downgrade() -> None:
    op.drop_table("recipes")
    with op.batch_alter_table("application_settings") as batch: batch.drop_column("main_menu_modules_json")
