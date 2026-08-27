from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.13.4"),
    ("SOURCE_INFO.json", '"version": "1.7.13.4"'),
    ("SOURCE_INFO.json", '"alembic_head": "0053"'),
    ("RELEASE_NOTES_1.7.13.4.md", "# DocOfHome 1.7.13.4"),
    ("frontend/src/types/settings.ts", "'images'"),
    ("frontend/src/types/settings.ts", "'documents'"),
    ("frontend/src/types/settings.ts", "'workloads'"),
    ("frontend/src/components/ModuleSettingsCard.vue", "Dienste & Container (Docker)"),
    ("frontend/src/App.vue", "visibleUtilityNavigation"),
    ("frontend/src/router/index.ts", "['/images', 'images']"),
    ("backend/app/schemas/settings.py", 'IMAGES = "images"'),
    ("backend/migrations/versions/0053_complete_module_navigation.py", 'main_menu_modules_json'),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.13.4-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.13.4 geprüft.")
