from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.10"),
    ("SOURCE_INFO.json", '"base_version": "1.7.9"'),
    ("frontend/src/content/handbook.ts", r"\`read\`"),
    ("frontend/src/content/handbook.ts", r"\`\`\`nginx"),
    ("backend/app/mcp_server.py", "def save_network_record("),
    ("RELEASE_NOTES_1.7.10.md", "# DocOfHome 1.7.10"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.10-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.10 geprüft.")
