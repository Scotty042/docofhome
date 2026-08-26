from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import Field, SQLModel


class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True, max_length=200)
    category: str = Field(default="", index=True, max_length=100)
    tags_json: str = Field(default="[]", sa_type=Text)
    preparation_minutes: int | None = Field(default=None, ge=0)
    cooking_minutes: int | None = Field(default=None, ge=0)
    servings: float = Field(default=4, gt=0)
    favorite: bool = Field(default=False, index=True)
    image_url: str | None = Field(default=None, max_length=1000)
    ingredients_json: str = Field(default="[]", sa_type=Text)
    steps_json: str = Field(default="[]", sa_type=Text)
    notes: str = Field(default="", sa_type=Text)
    source_url: str | None = Field(default=None, max_length=1000)
    attachments_json: str = Field(default="[]", sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

