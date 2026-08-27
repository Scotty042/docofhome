from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.13.2"),
    ("SOURCE_INFO.json", '"version": "1.7.13.2"'),
    ("frontend/src/App.vue", "{ key: 'cookbook', title: 'Kochbuch', icon: 'mdi-chef-hat', to: '/wiki/kochbuch' }"),
    ("RELEASE_NOTES_1.7.13.2.md", "# DocOfHome 1.7.13.2"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.13.2-Vertrag fehlt in {relative}: {marker}")
app = (root / "frontend/src/App.vue").read_text(encoding="utf-8")
submenu = 'v-if="enabledModules.has(\'cookbook\')" prepend-icon="mdi-chef-hat" title="Kochbuch" to="/wiki/kochbuch"'
if submenu in app:
    raise SystemExit("Kochbuch ist weiterhin doppelt im Wiki-Untermenü vorhanden")
print("DocOfHome-Releasevertrag 1.7.13.2 geprüft.")
