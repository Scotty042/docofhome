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
    image_url: str | None = Field(default=None, max_length=1000)
    ingredients: list[Ingredient] = Field(default_factory=list, max_length=500)
    steps: list[str] = Field(default_factory=list, max_length=200)
    notes: str = Field(default="", max_length=50000)
    source_url: HttpUrl | None = None
    attachments: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("title", "category")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.startswith("/") and not normalized.startswith("//"):
            return normalized
        if normalized.startswith("https://") or normalized.startswith("http://"):
            return normalized
        raise ValueError("Bild muss eine HTTP(S)-URL oder ein lokaler Pfad sein.")

class RecipeRead(RecipeWrite):
    id: UUID
    created_at: datetime
    updated_at: datetime



class RecipeImageUploadRead(BaseModel):
    image_url: str
    image_reference: str
