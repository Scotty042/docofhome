# DocOfHome 1.6.0 – Validierungsbericht

**Stand:** 27. Juli 2026  
**Ausgangsbasis:** `DocOfHome-1.5.0.zip`  
**Zielversion:** `1.6.0`  
**Alembic-Head:** `0037`

## Zusammenfassung

Der Quellstand wurde statisch geprüft und die Migrationen wurden isoliert gegen
SQLite ausgeführt. Die neuen Releaseverträge, die Python-Compileprüfung und die
Syntaxprüfung der geänderten TypeScript- beziehungsweise Vue-Scriptblöcke sind
erfolgreich.

Die vollständigen Frontend-, Backend- und Docker-Gates konnten in der
Arbeitsumgebung nicht ausgeführt werden, weil benötigte Pakete nicht vom
internen Paketproxy geladen werden konnten und kein Docker-Programm vorhanden
war. Sie werden daher ausdrücklich **nicht als bestanden** bewertet.

Der bereitgestellte Stand ist damit ein statisch und migrationsseitig geprüfter
Quellrelease. Vor einer produktiven Aktualisierung müssen die offenen Gates auf
einem Buildsystem mit funktionierenden Paketquellen und Docker nachgeholt
werden.

## Erfolgreich ausgeführte Prüfungen

### Projekt- und Versionsverträge

- zentrale Version `1.6.0` in `VERSION`;
- Backend-Paketversion `1.6.0`;
- eigene Frontend-Paketmetadaten `1.6.0`;
- transitive npm-Abhängigkeiten nicht pauschal versioniert;
- Alembic-Head ist Migration `0037`;
- sichtbarer Produktname mit `scripts/check-branding.py` geprüft;
- `git diff --check` ohne Whitespacefehler.

### Python und Releaseverträge

Ausgeführt:

```text
python3 -m compileall -q backend scripts
python3 scripts/check-branding.py
python3 scripts/check-release-1.2.4.py
python3 scripts/check-release-1.3.0.py
python3 scripts/check-release-1.3.1.py
python3 scripts/check-release-1.3.2.py
python3 scripts/check-release-1.4.0.py
python3 scripts/check-release-1.4.1.py
python3 scripts/check-release-1.4.2.py
python3 scripts/check-release-1.5.0.py
python3 scripts/check-release-1.6.0.py
```

Ergebnis: erfolgreich.

Der Releasevertrag 1.6.0 prüft unter anderem:

- Zurücksetzen der Integrationsmeldung im Assistenten;
- Abschlussnavigation und manuellen Fallback;
- neuen Backup-Präfix und Legacy-Kompatibilität;
- DuckDuckGo-/Wikimedia-Bildsuche;
- Filterung nicht elektrischer Zähler;
- kompakte Schrankansicht und Asset-Typ-Farben;
- Sicherungsautomat- und Stromstoßschalter-Stammdaten;
- Smart-Meter-Messpunkte und Home-Assistant-Zuordnungen;
- Handbucherweiterungen.

### Migrationen

Ausgeführt:

```text
python3 scripts/check-migration-0030.py
python3 scripts/check-migration-0031.py
python3 scripts/check-migration-0032.py
python3 scripts/check-migration-0033.py
python3 scripts/check-migration-0034.py
python3 scripts/check-migration-0035.py
python3 scripts/check-migration-0036.py
python3 scripts/check-migration-0037.py
```

Ergebnis: erfolgreich.

Migration `0037` wurde isoliert als Upgrade, Downgrade und erneutes Upgrade
geprüft. Sie ergänzt optionale Felder für Sicherungsautomaten und
Stromstoßschalter sowie neue Tabellen für CT-/Smart-Meter-Messpunkte. Bestehende
Datensätze werden nicht überschrieben.

### TypeScript- und Vue-Script-Syntax

Die geänderten `.ts`-Dateien und die `<script setup lang="ts">`-Blöcke der
geänderten Vue-Komponenten wurden mit TypeScript `transpileModule` syntaktisch
geprüft.

Ergebnis: erfolgreich.

Diese Prüfung ersetzt weder `vue-tsc --noEmit` noch die Vue-Template-Kompilierung
oder Vitest.

## Nicht vollständig ausführbare Prüfungen

### Frontend: npm, Vitest, vue-tsc und Vite

`npm ci --offline` wurde ausgeführt und scheiterte, weil das benötigte Paket
`why-is-node-running-2.3.0.tgz` nicht im lokalen Cache vorhanden war:

```text
npm error code ENOTCACHED
npm error request to .../why-is-node-running-2.3.0.tgz failed:
cache mode is 'only-if-cached' but no cached response is available.
```

Der interne npm-Paketproxy antwortete für dieses Paket zusätzlich mit HTTP 503.
Daher konnten folgende Prüfungen nicht zuverlässig gestartet werden:

```text
npm test
npm run build
vue-tsc --noEmit
vite build
```

Bewertung: **nicht ausgeführt / nicht bestanden behauptet**.

### Backend: Entwicklungsabhängigkeiten, Ruff, Mypy und Pytest

Die Installation aus `backend/requirements-dev.txt` scheiterte am internen
Python-Paketindex:

```text
ERROR: Could not find a version that satisfies the requirement
fastapi<0.117,>=0.116 (from versions: none)
ERROR: No matching distribution found for fastapi<0.117,>=0.116
```

In der vorhandenen globalen Python-Umgebung fehlten unter anderem `sqlmodel`,
`apscheduler`, `structlog`, `ruff` und `mypy`. Deshalb konnten folgende Gates
nicht vollständig ausgeführt werden:

```text
ruff check app tests
mypy app
python -m pytest -q
alembic upgrade head
alembic check
```

Die migrationsspezifischen SQLite-Prüfskripte liefen unabhängig davon
vollständig erfolgreich.

Bewertung der vollständigen Backend-Suite: **nicht ausgeführt / nicht bestanden
behauptet**.

### Docker

In der Arbeitsumgebung ist kein Docker-Programm installiert:

```text
bash: docker: command not found
```

Daher nicht ausgeführt:

```text
docker compose build --no-cache
docker compose up -d
Healthcheck
Logprüfung
praktische Browserprüfung im Container
```

Bewertung: **nicht ausgeführt / nicht bestanden behauptet**.

## Vor produktivem Einsatz nachzuholen

Auf einem geeigneten Buildsystem aus dem frisch entpackten Releasebestand:

```bash
cd frontend
npm ci
npm test
npm run build

cd ../backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/python -m pytest -q

cd ..
bash scripts/check.sh
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --no-color
```

Danach praktisch prüfen:

- Integrationsmeldungen beim Schrittwechsel;
- Abschluss des geführten Assistenten und Fallback-Button;
- Backup-Erstellung mit DocOfHome-Namen sowie Restore eines alten
  `tectoryn-backup-*`-Archivs;
- Online-Bildsuche mit realen Hersteller-/Modellbezeichnungen;
- Zählerschrank auf PC und Tablet;
- Filterung von Wasser- und Gaszählern;
- B16-/C16-Stammdaten und Stromstoßschalter;
- Smart-Meter-Messklemmen, Verkabelungszuordnung und Home-Assistant-Entitäten;
- bestehende Verteilungen, Verkabelungen, Bilder und Zählerstände nach Migration.
