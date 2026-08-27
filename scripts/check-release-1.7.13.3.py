from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.13.3"),
    ("SOURCE_INFO.json", '"version": "1.7.13.3"'),
    ("RELEASE_NOTES_1.7.13.3.md", "# DocOfHome 1.7.13.3"),
    ("frontend/src/components/RecipeEditorDialog.vue", "RecipeImageField"),
    ("frontend/src/components/RecipeImageField.vue", "Foto aufnehmen"),
    ("frontend/src/components/RecipeImageField.vue", "Aus Immich auswählen"),
    ("backend/app/api/v1/recipes.py", '/images/upload'),
    ("backend/app/services/recipe_images.py", 'recipe-images'),
    ("frontend/src/components/RecipeDetailDialog.vue", "ingredient-quantity"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.13.3-Vertrag fehlt in {relative}: {marker}")

editor = (root / "frontend/src/components/RecipeEditorDialog.vue").read_text(encoding="utf-8")
if 'label="Bild-URL (optional)"' in editor:
    raise SystemExit("Normales Bild-URL-Feld ist weiterhin im Rezepteditor vorhanden")
print("DocOfHome-Releasevertrag 1.7.13.3 geprüft.")
