# Validierungsbericht DocOfHome 1.3.1

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.3.0  
Zielversion: DocOfHome 1.3.1  
Alembic-Head: `0032`

## 1. Umgesetzter Umfang

- Darstellung normaler DIN-Assets direkt im TE-Raster;
- Drag-and-drop für Schutzgeräte und normale DIN-Assets in einfacher und
  strukturierter Reihenaufteilung;
- gemeinsame Kollisionsprüfung mit passiven Schrankkomponenten;
- optionale DIN-Breite an Asset-Typ und Asset ohne Produktpflicht;
- wirksame Breitenreihenfolge Asset, DIN-Produkt, Asset-Typ;
- automatische Übernahme dieser Breite für Sicherungen, FI/RCD und andere
  Schutzgeräte;
- mehrere eingehende Versorgungsverbindungen an einer Schrankkomponente;
- Leiterprüfung für konfigurierte und tatsächlich eingespeiste Phasen;
- Anzeige aller Einspeisungen in Topologie und Inline-Verkabelungsübersicht;
- laufender Verbrauchsmonat bis heute mit tagesbezogener Endabdeckung;
- Migration `0032`.

## 2. Erfolgreich ausgeführte Prüfungen

- `python -m compileall -q backend/app backend/tests backend/migrations/versions scripts`
- `python scripts/check-version.py`
- `python scripts/check-release-1.2.4.py`
- `python scripts/check-release-1.3.0.py`
- `python scripts/check-release-1.3.1.py`
- statische Vertragsprüfung der vollständigen `AssetWrite`-Initialisierung auf der Home-Assistant-Seite;
- `python scripts/check-migration-0030.py`
- `python scripts/check-migration-0031.py`
- `python scripts/check-migration-0032.py`
- statische TypeScript-Syntaxprüfung der geänderten `.ts`-Dateien und der
  `<script setup>`-Blöcke der geänderten Vue-Dateien mit dem lokal vorhandenen
  TypeScript-Compiler;
- Prüfung der geänderten Python-Dateien auf Zeilen über 100 Zeichen;
- Prüfung auf verbotene Cache-, Build-, Datenbank- und Secret-Dateien;
- Entpacken des finalen ZIP und Prüfung jeder Manifestposition auf Dateigröße
  und SHA-256.

Migration `0032` wurde gegen eine repräsentative SQLite-Datenbank als Upgrade,
Downgrade und erneutes Upgrade ausgeführt.

## 3. Enthaltene Regressionstests

Der Quellstand enthält Tests für:

- Breite vom Asset-Typ und direkte Überschreibung am Asset;
- Übernahme der Asset-Typbreite beim Anlegen und Platzieren eines Schutzgeräts;
- Ablehnung eines Assets ohne wirksame DIN-Breite;
- Ablehnung einer von der Stammdatenbreite abweichenden Platzierungsbreite;
- Mehrfacheinspeisung eines L1/L2/L3-Phasenverteilerblocks;
- Sperre einer Einspeisungsänderung, wenn dadurch Abgänge unversorgt wären;
- Ablehnung von L2 als Ausgang, wenn nur L1 eingespeist wird;
- Ablehnung nicht konfigurierter Leiter wie N;
- Anzeige mehrerer Einspeisungen im Frontend;
- vollständigen laufenden Monat nach einer heutigen Ablesung;
- Darstellung und Drag-and-drop normaler DIN-Assets im Reihenraster.

## 4. Nicht ausführbare Prüfungen in dieser Umgebung

### Frontend

Der auf dem Zielsystem gemeldete TypeScript-Fehler TS2345 in
`SmartHomePage.vue` wurde durch die fehlende Initialisierung von `module_width`
verursacht und im Quellstand korrigiert. Alle weiteren Stellen, die
`AssetWrite` unmittelbar erzeugen, wurden auf dieses Pflichtfeld geprüft.

Ein erneuter lokaler `npm ci --no-audit --no-fund` scheiterte jedoch weiterhin
an der konfigurierten Paketquelle mit HTTP 503 beim Paket
`why-is-node-running` 2.3.0. Deshalb konnten `npm test`, `vue-tsc --noEmit` und
`vite build` in dieser Umgebung nicht erneut vollständig ausgeführt werden.
Der korrigierte Docker-Build auf dem Zielsystem bleibt die verbindliche
Endprüfung.

### Backend

Für den vollständigen Backend-Testlauf fehlt in der Umgebung das Projektpaket
`sqlmodel`; außerdem stehen Ruff und mypy nicht zur Verfügung. Die enthaltenen
Pytest-Tests konnten deshalb nicht vollständig ausgeführt werden. Python-Syntax
und die eigenständigen Migrationsprüfungen wurden dagegen tatsächlich
abgeschlossen.

### Docker

Docker oder Podman ist nicht verfügbar. Image-Build, Containerstart,
Healthcheck und praktische Browserprüfung müssen auf dem Zielsystem erfolgen.

## 5. Verbindliche Zielsystemprüfung

```bash
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Danach mindestens prüfen:

1. Smart Meter mit 4 TE im Raster und nicht unterhalb der Schiene;
2. Drag-and-drop desselben Assets innerhalb und zwischen Reihen;
3. Kollision mit Schutzgerät oder Phasenverteilerblock;
4. Asset-Typbreite ohne Produktstammsatz;
5. zwei Einspeisungen an einem Phasenverteilerblock;
6. Ablehnung eines L1-zu-L2-Fehlers;
7. aktueller Verbrauchsmonat nach heutiger Ablesung;
8. Backend-Logs ohne Migrationsexception oder HTTP 500.

## 6. Bewertung

Der Stand ist als Release Candidate für DocOfHome 1.3.1 paketiert. Statische
Prüfungen, Migrationsprüfung und Paketintegrität sind erfolgreich. Die endgültige
Freigabe hängt vom vollständigen Frontend-/Backend-/Docker-Lauf auf dem
Zielsystem ab.
