from pathlib import Path

path = Path(__file__).resolve().parents[1] / "backend/migrations/versions/0056_integration_browser_urls.py"
source = path.read_text(encoding="utf-8")
for marker in (
    'revision: str = "0056"',
    'down_revision: str | None = "0055"',
    'sa.Column("browser_url", sa.String(length=2048), nullable=True)',
    'batch.drop_column("browser_url")',
):
    if marker not in source:
        raise SystemExit(f"Migration 0056 unvollständig: {marker}")
print("Migration 0056 statisch geprüft.")
