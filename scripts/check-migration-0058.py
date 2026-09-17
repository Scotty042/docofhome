from pathlib import Path

source = (
    Path(__file__).resolve().parents[1]
    / "backend/migrations/versions/0058_multi_docker_hosts_ssh.py"
).read_text(encoding="utf-8")
for marker in (
    'revision = "0058"',
    'down_revision = "0057"',
    '"docker_hosts"',
    '"connection_type"',
    '"ssh_host_key"',
    '"uq_docker_hosts_asset"',
    'name="Lokaler Docker-Host"',
):
    assert marker in source, marker
print("Migration 0058: Mehrhost- und SSH-Konfiguration statisch geprüft.")
