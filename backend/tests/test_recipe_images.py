from pathlib import Path

from app.schemas.recipe import RecipeWrite


def test_recipe_image_url_accepts_local_paths() -> None:
    payload = RecipeWrite(title="Test", image_url="/api/v1/recipes/images/test.webp")
    assert payload.image_url == "/api/v1/recipes/images/test.webp"


def test_recipe_image_url_rejects_non_url_text() -> None:
    try:
        RecipeWrite(title="Test", image_url="kein bildpfad")
    except ValueError:
        return
    raise AssertionError("Ungültiger Bildpfad wurde akzeptiert")


def test_recipe_image_service_uses_own_directory() -> None:
    source = Path(__file__).parents[1] / "app" / "services" / "recipe_images.py"
    text = source.read_text(encoding="utf-8")
    assert '"recipe-images"' in text
    assert '"/api/v1/recipes/images/{reference}"' not in text
