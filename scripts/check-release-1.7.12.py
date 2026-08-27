from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.12"),
    ("SOURCE_INFO.json", '"base_version": "1.7.11"'),
    ("backend/app/mcp_server.py", "ingredients: list[Ingredient] | None"),
    ("backend/app/mcp_server.py", '"created": created'),
    ("backend/tests/test_mcp_recipe_contract.py", 'assert "payload" not in names'),
    ("RELEASE_NOTES_1.7.12.md", "# DocOfHome 1.7.12"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.12-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.12 geprüft.")
