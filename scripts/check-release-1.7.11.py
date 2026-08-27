from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    ("VERSION", "1.7.11"),
    ("SOURCE_INFO.json", '"base_version": "1.7.10"'),
    ("backend/app/mcp_server.py", 'return {"items": items, "count": len(items)}'),
    ("backend/tests/test_mcp_recipe_contract.py", '(query or "").strip()'),
    ("RELEASE_NOTES_1.7.11.md", "# DocOfHome 1.7.11"),
]
for relative, marker in required:
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"1.7.11-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.11 geprüft.")
