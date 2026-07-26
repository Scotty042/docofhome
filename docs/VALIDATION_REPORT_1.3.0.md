# Validierungsbericht DocOfHome 1.3.0

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.2.4  
Zielversion: DocOfHome 1.3.0  
Alembic-Head: `0031`

## 1. Umgesetzter Umfang

- passive Schrankkomponenten als eigene, nicht als Asset geführte Objekte;
- Typen für Phasenverteilerblock, Sammel-/Phasenschiene, N-/PE-Schiene,
  Reihen-/Anschlussklemme, Potentialverteiler und sonstige Komponenten;
- Platzierung über Reihe, TE-Startposition und TE-Breite in einfachen Reihen
  sowie in strukturierten Gerätebereichen;
- Zuordnung von `L1`, `L2`, `L3`, `N` und `PE` sowie optionalen technischen
  Angaben und der Zahl der Abgänge;
- Endpunkttyp `cabinet_component` für Elektro-Verkabelung und Topologie;
- gemeinsame Kollisionsprüfung für Schutzgeräte, DIN-Assets und passive
  Schrankkomponenten;
- Drag-and-drop von Schutzgeräten in Verteilungen mit einfacher
  Reihenaufteilung;
- Serienplatzierung in einfacher Reihenaufteilung ohne DIN-Bereichspflicht;
- Migration `0031` für Datenmodell und Endpunkttypen.

## 2. Erfolgreich ausgeführte Prüfungen

### Quellstand und Versionen

- `python scripts/check-version.py`
- `python scripts/check-release-1.2.4.py`
- `python scripts/check-release-1.3.0.py`
- Versionsabgleich von `VERSION`, Backend und Frontend: erfolgreich
- Prüfung auf Python-Zeilen über 100 Zeichen in den geänderten Dateien:
  ohne Treffer

### Python- und Frontend-Quellsyntax

- `python -m compileall -q backend/app backend/migrations scripts`
- zusätzliche `py_compile`-Prüfung der zentralen Layoutlogik
- TypeScript-Syntaxprüfung aller `.ts`-Dateien und aller Scriptblöcke der
  Vue-Dateien mit dem lokal vorhandenen TypeScript-Parser
- HTML-Fragmentprüfung der Templates von
  `ElectricalDistributionLayoutPage.vue` und `AssetDuplicateDialog.vue`

Diese Prüfungen bestätigen die syntaktische Lesbarkeit des Quellcodes. Sie
ersetzen nicht den vollständigen Lauf von `vue-tsc`, Vite oder Pytest.

### Migrationen

- `python scripts/check-migration-0030.py`
- `python scripts/check-migration-0031.py`
- Upgrade, Downgrade und erneutes Upgrade von Migration `0031` gegen eine
  repräsentative SQLite-Ausgangsdatenbank mit SQLAlchemy/Alembic
- dabei geprüft:
  - Tabelle `electrical_cabinet_components` wird erstellt und entfernt;
  - `electrical_asset_placements.area_id` wird nullable und beim Downgrade
    wieder verpflichtend;
  - `cabinet_component` wird in den Check-Constraints der Elektroverbindungen
    zugelassen und beim Downgrade wieder entfernt.

### Releasepaket

Nach Erstellung des finalen Pakets wurden zusätzlich ausgeführt:

- Entpacken des ZIP in einen neuen Prüfpfad;
- Prüfung jeder Manifestposition auf Pfad, Dateigröße und SHA-256;
- Prüfung auf nicht erlaubte Cache-, Build-, Datenbank- und Secret-Dateien;
- erneuter Lauf der statischen Versions-, Release-, Migrations- und
  Syntaxprüfungen aus dem entpackten Bestand.

## 3. Enthaltene Regressionstests

Der Quellstand enthält neue beziehungsweise angepasste Tests für:

- Schutzgeräteplatzierung im Reihenmodus mit `area_id = null`;
- passive Schrankkomponenten und ihre Leiterzuordnung;
- gemeinsame TE-Kollisionsprüfung;
- Bereitstellung von Schrankkomponenten als Verkabelungsendpunkte;
- Sperre beim Archivieren einer noch verkabelten Schrankkomponente;
- Serienplatzierung ohne DIN-Bereich im Reihenmodus;
- Frontend-Verträge für Reihen-Drag-and-drop und Schrankkomponenten.

Die Tests sind im Release enthalten, konnten in dieser Umgebung jedoch nicht
mit dem vollständigen Projekt-Dependency-Set ausgeführt werden.

## 4. Nicht ausführbare Prüfungen

### Frontend-Build und Vitest

`npm ci`, `npm test`, `vue-tsc --noEmit` und `vite build` konnten nicht
vollständig ausgeführt werden. Die konfigurierte npm-Paketquelle antwortete bei
der Abhängigkeitsabfrage mit:

```text
503 Service Temporarily Unavailable
```

Dadurch standen die lokalen Projektpakete einschließlich `vue-tsc`, Vite und
Vitest nicht zur Verfügung. Es wird deshalb ausdrücklich **nicht** behauptet,
dass der vollständige Frontend-Build in dieser Umgebung bestanden hat.

### Backend-Pytest, Ruff und mypy

Die Umgebung enthält SQLAlchemy, Alembic und Pytest, aber nicht die für den
vollständigen Anwendungslauf erforderlichen Pakete `sqlmodel`, `ruff` und
`mypy`. Deshalb konnten weder der komplette Backend-Testlauf noch Ruff und mypy
ausgeführt werden. Die Migration wurde unabhängig davon mit einer
repräsentativen SQLite-Struktur geprüft.

### Docker

In der Releaseumgebung ist weder Docker noch Podman verfügbar. Ein
`docker compose build`, Containerstart, Healthcheck und die praktische Prüfung
in der gebauten Anwendung waren daher nicht möglich.

## 5. Verbindliche Zielsystemprüfung vor produktivem Einsatz

Im Zielsystem sind mindestens auszuführen:

```bash
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Zusätzlich praktisch prüfen:

1. Unterverteilung im Modus **Einfache Reihen** öffnen und ein Schutzgerät per
   Drag-and-drop auf eine freie TE-Position verschieben.
2. Eine Serie von Sicherungen in einer Reihenverteilung anlegen; es darf kein
   DIN-Bereich verlangt werden.
3. Einen **Phasenverteilerblock L1/L2/L3** als Schrankkomponente anlegen und auf
   der DIN-Schiene positionieren.
4. Verbindungen wie
   `Netzanschluss → Vorsicherung → Zähler → Phasenverteilerblock → Unterverteilung`
   anlegen.
5. Weitere Abgänge vom Phasenverteilerblock zu Unterverteilungen, PV-Anlage und
   Sammelschiene erfassen.
6. Überschneidende TE-Platzierungen müssen kontrolliert abgewiesen werden.
7. Eine verkabelte Schrankkomponente darf erst nach Entfernen ihrer Verbindungen
   archiviert werden.
8. Backend-Logs auf Migration-, Validierungs- oder HTTP-500-Fehler prüfen.

## 6. Bewertung

Der Quellstand ist als **Release Candidate für DocOfHome 1.3.0** paketiert. Die
statischen Prüfungen, die repräsentative Migrationsprüfung und die
Manifestprüfung sind erfolgreich. Die endgültige Freigabe hängt noch vom
vollständigen npm-/Vite-/Vitest-Lauf, Backend-Testlauf und Docker-Praxistest im
Zielsystem ab.
