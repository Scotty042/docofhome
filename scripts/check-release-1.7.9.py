from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.9"),
    ("SOURCE_INFO.json", '"base_version": "1.7.8"'),
    ("backend/app/mcp_server.py", "def search_recipes("),
    ("backend/app/mcp_server.py", "def save_network_record("),
    ("backend/tests/test_mcp_domain_tools.py", "McpPermission.ADMIN"),
    ("RELEASE_NOTES_1.7.9.md", "# DocOfHome 1.7.9"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.9-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.9 geprüft.")
