from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = {
    "VERSION": "1.7.7",
    "SOURCE_INFO.json": '"alembic_head": "0052"',
    "frontend/public/manifest.webmanifest": '"display": "standalone"',
    "frontend/public/service-worker.js": "Network-first",
    "backend/migrations/versions/0052_cookbook_and_navigation.py": 'revision: str = "0052"',
    "frontend/src/content/handbook.ts": "docofhome.subdomain.conf",
}
for relative, marker in required.items():
    content = (root / relative).read_text(encoding="utf-8")
    if marker not in content:
        raise SystemExit(f"1.7.7-Vertrag fehlt in {relative}: {marker}")
print("DocOfHome-Releasevertrag 1.7.7 geprüft.")
