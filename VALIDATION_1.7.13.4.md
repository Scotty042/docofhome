# Validierung DocOfHome 1.7.13.4

Stand: 27.08.2026

## Geprüfte Änderungen

- `images`, `documents` und `workloads` sind Frontend- und Backend-seitig gültige `ModuleKey`-Werte.
- Die Modulübersicht enthält **Bilder**, **Dokumente** und **Dienste & Container (Docker)**.
- Die drei Hauptmenüeinträge verwenden dieselbe Aktiv-/Hauptmenü-Logik wie die übrigen Module.
- Der Router blockiert die direkten Routen deaktivierter Module.
- Migration `0053` übernimmt bestehende Installationen ohne sichtbare Menüänderung und ergänzt beide Modul-Listen.

## Ausgeführte Prüfungen

- Versionskonsistenz 1.7.13.4: erfolgreich.
- Branding-Prüfung: erfolgreich.
- Releasevertrag 1.7.13.4: erfolgreich.
- Python-Syntax für Backend und Migrationen: erfolgreich.
- 195 TypeScript-/Vue-Skripteinheiten syntaktisch geprüft.
- Migration `0052`: statischer Vertragscheck erfolgreich.
- Migration `0053`: statischer Vertragscheck erfolgreich.
- Migration `0053`: Upgrade und Downgrade gegen SQLite mit vorhandenen Modulwerten erfolgreich geprüft.

## In dieser Umgebung nicht vollständig ausführbar

Der vollständige Pytest-/Mypy-/Ruff- und Vite-Testlauf konnte hier nicht ausgeführt werden,
weil insbesondere `sqlmodel` und `frontend/node_modules` in der isolierten Umgebung fehlen.
Die vorhandenen Projektprüfungen bleiben in `scripts/check.sh` hinterlegt.

Alembic-Head: `0053`
