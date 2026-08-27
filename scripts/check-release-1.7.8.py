from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = {
    "VERSION": "1.7.8",
    "SOURCE_INFO.json": '"base_version": "1.7.7"',
    "backend/app/main.py": 'app.add_route("/mcp/{token}"',
    "backend/app/mcp_server.py": 'path.removeprefix("/mcp/")',
    "frontend/src/utils/clipboard.ts": "document.execCommand('copy')",
    "frontend/src/components/SafeMarkdown.vue": "code-window",
    "frontend/src/pages/SettingsPage.vue": "Ungespeicherte Änderungen",
    "RELEASE_NOTES_1.7.8.md": "# DocOfHome 1.7.8",
}
for relative, marker in required.items():
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.8-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.8 geprüft.")
