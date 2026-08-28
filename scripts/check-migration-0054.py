from pathlib import Path

path = Path(__file__).resolve().parents[1] / "backend/migrations/versions/0054_docker_sync.py"
content = path.read_text(encoding="utf-8")
markers = (
    'revision: str = "0054"',
    'down_revision: str | None = "0053"',
    'docker_sync_settings',
    'docker_container_id',
    'docker_networks_json',
    'docker_mounts_json',
    'refresh_interval_seconds',
)
for marker in markers:
    if marker not in content:
        raise SystemExit(f"Migration 0054 unvollständig: {marker}")
print("Migration 0054 statisch geprüft.")
