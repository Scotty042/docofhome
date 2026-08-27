from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.13"),
    ("SOURCE_INFO.json", '"base_version": "1.7.12"'),
    ("frontend/src/pages/CookbookPage.vue", "RecipeCookMode"),
    ("frontend/src/pages/CookbookPage.vue", "ingredientSuggestions"),
    ("frontend/src/components/RecipeCookMode.vue", "Bildschirm nicht abschalten"),
    ("frontend/src/components/RecipeCookMode.vue", "100dvh"),
    ("frontend/src/components/RecipeEditorDialog.vue", "mdi-drag-vertical"),
    ("frontend/src/components/RecipeEditorDialog.vue", "Nach oben"),
    ("frontend/src/components/RecipeDetailDialog.vue", "Kochmodus"),
    ("frontend/src/pages/cookbook1713.test.ts", "cookbook tablet experience"),
    ("RELEASE_NOTES_1.7.13.md", "# DocOfHome 1.7.13"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.13-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.13 geprüft.")
