from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.7.14"

assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION
assert f'"version": "{VERSION}"' in (ROOT / "frontend/package.json").read_text(encoding="utf-8")
assert f'version = "{VERSION}"' in (ROOT / "backend/pyproject.toml").read_text(encoding="utf-8")
assert f'docofhome-shell-{VERSION}' in (ROOT / "frontend/public/service-worker.js").read_text(encoding="utf-8")

source = json.loads((ROOT / "SOURCE_INFO.json").read_text(encoding="utf-8"))
assert source["version"] == VERSION
assert source["alembic_head"] == "0054"
assert source["release_notes"] == "PROJECT_HISTORY.md"

history = (ROOT / "PROJECT_HISTORY.md").read_text(encoding="utf-8")
for marker in (
    "## 1.7.14 – 2026-08-28",
    "Docker Engine",
    "Migration `0054`",
    "Netzwerk-IP-Abgleich",
    "Release-Manifest",
    "Validierung",
):
    assert marker in history, marker

# Fragmented release-history files must no longer return to the project root.
for pattern in (
    "CHANGELOG.md",
    "RELEASE_NOTES_*.md",
    "IMPLEMENTATION_SUMMARY_*.md",
    "RELEASE_MANIFEST_*.json",
    "VALIDATION_*.md",
):
    assert not list(ROOT.glob(pattern)), f"Historische Einzeldateien gefunden: {pattern}"

workloads = (ROOT / "frontend/src/pages/WorkloadsPage.vue").read_text(encoding="utf-8")
for marker in ("Jetzt aktualisieren", "Aktualisierungsintervall", "Docker-Socket", "Letzter Erfolg"):
    assert marker in workloads, marker

network = (ROOT / "frontend/src/pages/NetworkPage.vue").read_text(encoding="utf-8")
for marker in ("sortIpTable('device')", "sortIpTable('documented')", "ipSortIcon"):
    assert marker in network, marker

dashboard = (ROOT / "frontend/src/pages/DashboardPage.vue").read_text(encoding="utf-8")
assert "meter-reading:" in dashboard
assert "visibleCriticalItems" in dashboard

print(f"Releasevertrag {VERSION} geprüft.")
