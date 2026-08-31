from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.7.16"

assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION
assert f'"version": "{VERSION}"' in (ROOT / "frontend/package.json").read_text(encoding="utf-8")
assert f'version = "{VERSION}"' in (ROOT / "backend/pyproject.toml").read_text(encoding="utf-8")
assert f'docofhome-shell-{VERSION}' in (ROOT / "frontend/public/service-worker.js").read_text(encoding="utf-8")

source = json.loads((ROOT / "SOURCE_INFO.json").read_text(encoding="utf-8"))
assert source["version"] == VERSION
assert source["base_version"] == "1.7.15"
assert source["alembic_head"] == "0055"
assert source["release_notes"] == "PROJECT_HISTORY.md"

history = (ROOT / "PROJECT_HISTORY.md").read_text(encoding="utf-8")
for marker in (
    "## 1.7.16 – 2026-08-31",
    "Lebenslauf",
    "Paperless-ngx",
    "Migration `0055`",
    "work_item_event_paperless_links",
    "automatische Zuordnung ist bewusst nicht",
):
    assert marker in history, marker

for pattern in (
    "CHANGELOG.md",
    "RELEASE_NOTES_*.md",
    "IMPLEMENTATION_SUMMARY_*.md",
    "RELEASE_MANIFEST_*.json",
    "VALIDATION_*.md",
):
    assert not list(ROOT.glob(pattern)), f"Historische Einzeldateien gefunden: {pattern}"

maintenance = (ROOT / "frontend/src/pages/MaintenancePage.vue").read_text(encoding="utf-8")
for marker in (
    "Zeitstrahl & Profil",
    "Fahrzeugart (PKW, Motorrad …)",
    "Paperless-Dokument verknüpfen",
    "TÜV",
    "Schornsteinfeger",
):
    assert marker in maintenance, marker

paperless = (ROOT / "backend/app/connectors/paperless.py").read_text(encoding="utf-8")
for marker in ('Authorization', 'Token {self.token}', '/api/documents/', 'params["text"]'):
    assert marker in paperless, marker

work_service = (ROOT / "backend/app/services/work.py").read_text(encoding="utf-8")
for marker in ("def subject_timeline", "paperless_links", "activity_kind"):
    assert marker in work_service, marker

# Keep 1.7.14 contracts that remain part of the release.
workloads = (ROOT / "frontend/src/pages/WorkloadsPage.vue").read_text(encoding="utf-8")
for marker in ("Jetzt aktualisieren", "Aktualisierungsintervall", "Docker-Socket", "Letzter Erfolg"):
    assert marker in workloads, marker
network = (ROOT / "frontend/src/pages/NetworkPage.vue").read_text(encoding="utf-8")
for marker in ("sortIpTable('device')", "sortIpTable('documented')", "ipSortIcon"):
    assert marker in network, marker

print(f"Releasevertrag {VERSION} geprüft.")
