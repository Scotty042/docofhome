from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, field_validator

class Ingredient(BaseModel):
    amount: float | None = Field(default=None, ge=0)
    unit: str = Field(default="", max_length=30)
    name: str = Field(min_length=1, max_length=200)
    note: str = Field(default="", max_length=300)

class RecipeWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="", max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=30)
    preparation_minutes: int | None = Field(default=None, ge=0, le=10000)
    cooking_minutes: int | None = Field(default=None, ge=0, le=10000)
    servings: float = Field(default=4, gt=0, le=1000)
    favorite: bool = False
    image_url: HttpUrl | None = None
    ingredients: list[Ingredient] = Field(default_factory=list, max_length=500)
    steps: list[str] = Field(default_factory=list, max_length=200)
    notes: str = Field(default="", max_length=50000)
    source_url: HttpUrl | None = None
    attachments: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("title", "category")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

class RecipeRead(RecipeWrite):
    id: UUID
    created_at: datetime
    updated_at: datetime

