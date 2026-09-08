"""Repair blank recipe titles without deleting ingredients or instructions."""

import sqlalchemy as sa
from alembic import op

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, title FROM recipes")).fetchall()
    for recipe_id, title in rows:
        if not title or not title.strip():
            connection.execute(
                sa.text("UPDATE recipes SET title = :title WHERE id = :id"),
                {"id": recipe_id, "title": f"Wiederhergestelltes Rezept {recipe_id}"},
            )
    with op.batch_alter_table("recipes") as batch:
        batch.create_check_constraint("ck_recipes_title_not_blank", "length(trim(title)) >= 1")


def downgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.drop_constraint("ck_recipes_title_not_blank", type_="check")
