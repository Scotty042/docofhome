# Validierungsbericht – DocOfHome 1.0.0 Fixstand 2

Stand: 23. Juli 2026

## Erfolgreich geprüft

- ZIP-Ausgangsstand und Projektstruktur
- Python-Syntax aller Backend-, Migrations- und Testmodule mit `compileall`
- TypeScript-Syntax und interne Typbezüge aller `.ts`-Dateien sowie aller
  `<script setup lang="ts">`-Blöcke unter den strikten Projekteinstellungen
- Vue-Templates der geänderten Oberfläche auf doppelte Attribute geprüft
- gegenüber dem geprüften 1.0.0-Ausgangsstand keine neuen MDI-Icon-Namen
  eingeführt; der vorhandene Satz von 207 Icons bleibt unverändert
- zentrale Version mit `scripts/check-version.py`
- sichtbares Branding mit `scripts/check-branding.py`
- neue beziehungsweise angepasste Regressionstests für Suchkürzel,
  Location-Routen und lesbare Audit-Kontexte
- frische Extraktion des Release-ZIPs sowie erneute Syntax-, Versions-,
  Branding- und Manifestprüfung

## In dieser isolierten Arbeitsumgebung nicht vollständig ausführbar

Der NPM-Paketproxy antwortete während der Validierung wiederholt mit HTTP 503.
Dadurch konnten `npm ci`, der echte `vue-tsc`-Lauf, Vite-Build und Vitest hier
nicht vollständig ausgeführt werden. Der Python-Paketindex stellte außerdem die
festgelegten Projektabhängigkeiten nicht bereit, weshalb Pytest, Ruff, mypy und
die Alembic-Laufzeitprüfung in dieser Umgebung nicht wiederholt werden konnten.
Eine Docker-Engine ist auf dem Prüfhost nicht installiert.

Der Docker-Build auf dem Zielsystem bleibt deshalb das finale Laufzeit-Gate:

```bash
docker compose build --no-cache
docker compose up -d
```

Die im Paket enthaltenen Prüfskripte und CI-Definitionen bleiben unverändert
verfügbar.
