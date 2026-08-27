from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.settings import settings

MAX_RECIPE_IMAGE_BYTES = 10 * 1024 * 1024
SUPPORTED_RECIPE_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class RecipeImageError(RuntimeError):
    """Base error for locally stored recipe images."""


class RecipeImageValidationError(RecipeImageError):
    """Raised when an image cannot be accepted or decoded."""


class RecipeImageService:
    @property
    def upload_dir(self) -> Path:
        return settings.data_dir / "uploads" / "recipe-images"

    async def upload(self, upload: UploadFile) -> tuple[str, str]:
        content_type = (upload.content_type or "").lower()
        if content_type not in SUPPORTED_RECIPE_IMAGE_TYPES:
            raise RecipeImageValidationError(
                "Unterstützt werden JPEG-, PNG- und WebP-Bilder."
            )
        content = await upload.read(MAX_RECIPE_IMAGE_BYTES + 1)
        if not content:
            raise RecipeImageValidationError("Die hochgeladene Bilddatei ist leer.")
        if len(content) > MAX_RECIPE_IMAGE_BYTES:
            raise RecipeImageValidationError("Das Rezeptbild darf höchstens 10 MB groß sein.")
        return self.store(content)

    def store(self, content: bytes) -> tuple[str, str]:
        try:
            with Image.open(BytesIO(content)) as source:
                source.load()
                image = source.convert("RGB")
                image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, format="WEBP", quality=86, method=6, optimize=True)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise RecipeImageValidationError(
                "Die Datei ist kein gültiges unterstütztes Bild."
            ) from exc

        optimized = output.getvalue()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(optimized).hexdigest()[:16]
        reference = f"{digest}-{uuid4().hex[:12]}.webp"
        (self.upload_dir / reference).write_bytes(optimized)
        return f"/api/v1/recipes/images/{reference}", reference

    def resolve(self, reference: str) -> Path:
        safe_name = Path(reference).name
        if safe_name != reference or not safe_name:
            raise RecipeImageValidationError("Ungültiger Rezeptbildpfad.")
        candidate = (self.upload_dir / safe_name).resolve()
        root = self.upload_dir.resolve()
        if root not in candidate.parents or not candidate.is_file():
            raise RecipeImageValidationError("Rezeptbild wurde nicht gefunden.")
        return candidate
