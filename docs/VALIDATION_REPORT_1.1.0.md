# Validierungsbericht – DocOfHome 1.1.0

Stand: 23. Juli 2026  
Ausgangspaket: `DocOfHome-v1.0.0-fix2(1).zip`  
Arbeitsweise: ausschließlich lokale Dateien und lokal vorhandene Werkzeuge

## Erfolgreich ausgeführt

- Ausgangs-ZIP separat extrahiert und den 1.1.0-Stand dagegen abgeglichen;
  keine Datei des Fix2-Ausgangsstands wurde entfernt.
- Python-Syntax aller Backend-, Migrations- und Testmodule mit `compileall`
  geprüft.
- zentrale Version `1.1.0` in `VERSION`, Backend-Metadaten,
  `frontend/package.json` und `frontend/package-lock.json` geprüft.
- sichtbares Produkt-Branding mit `scripts/check-branding.py` geprüft.
- vollständige Alembic-Migrationskette `0001 -> 0027` direkt gegen eine lokale
  SQLite-Datenbank ausgeführt.
- Migration `0027` technisch auf `0026` zurückgesetzt und erneut auf `0027`
  aktualisiert.
- separaten Nutzdatentest `0026 -> 0027` ausgeführt; vorhandene Assets,
  Verbrauchszähler und Elektroverbindungen blieben erhalten.
- nach Migration `0027` einen Zähler des Typs `electricity_feed_in` sowie zwei
  verschiedene aktive Quellen auf demselben Elektro-Topologie-Ziel angelegt.
- Energiebilanz-Rechenkomponente lokal ausgeführt: Hausverbrauch,
  Eigenverbrauch, Autarkiegrad, Eigenverbrauchsquote und die Kennzeichnung
  physikalisch inkonsistenter Eingangswerte geprüft.
- Pydantic-Validierung der Energie-Konfiguration und Energiekomponenten lokal
  ausgeführt.
- eigenständig kompilierbare TypeScript-Module unter strikten Einstellungen
  geprüft.
- TypeScript-Syntax aller `.ts`-Dateien und aller Vue-`script setup`-Blöcke
  geprüft; die geänderten Vue-Skripte wurden zusätzlich mit lokalen
  Framework-Stubs streng typgeprüft.
- geänderte Vue-Dateien auf Grundstruktur und doppelte Attribute geprüft.
- Frontend-Logik für eigene Diagrammskalierung je Serie und mehrere eingehende
  Topologieverbindungen kompiliert und mit Node ausgeführt.
- gegenüber dem geprüften Fix2-Ausgangsstand keine neuen MDI-Icon-Namen
  eingeführt.
- statische Regressionen der Fix2-Funktionen geprüft: Gebäudestruktur-Assistent,
  globaler Suchfokus und `/`-Kürzel, Dashboard-Drag-and-Drop, FRITZ!Box-Hostliste
  und MAC-Zuordnung, lesbare Änderungshistorie und durchsuchbare Asset-Auswahl.
- Sprint-0038-Verträge geprüft: Einspeisezähler, Primärzählerübernahme und
  Fallback, Ableseerinnerungen, visuelle Immich-Auswahl, Energie-API,
  Mehrquellen-Topologie und Migration `0027`.
- Shell-Skripte auf Unix-Zeilenenden normalisiert und als ausführbar markiert.
- Release-ZIP nach der Erzeugung vollständig getestet, erneut extrahiert und
  gegen das interne SHA-256-Manifest geprüft.

## Im Quellstand enthaltene Regressionstests

- Energiebilanz aus Netzbezug, PV-Erzeugung und Netzeinspeisung;
- mehrere PV-Quellen, Wechselrichter und Speicher;
- Primärzählerübernahme und deterministischer Fallback für Strom und Gas;
- Mehrquellen-Topologie, Zyklus- und Doppelverbindungsverbot;
- Migrationstabellen und parallele Einspeisungen;
- eigene Statistikskalierung je Verbrauchsserie.

## In dieser lokalen Umgebung nicht vollständig ausführbar

Die gelieferte ZIP enthält weder installierte Python-Abhängigkeiten noch
`frontend/node_modules`. Lokal fehlen insbesondere `sqlmodel`, `ruff`, `mypy`,
`vue-tsc`, Vite und Vitest. Entsprechend konnten die vollständigen
Dependency-basierten Läufe `pytest`, Ruff, mypy, `npm test` und
`npm run build` nicht ausgeführt werden. Es wurden keine Pakete aus externen
Quellen nachgeladen, weil ausdrücklich ausschließlich lokal mit der ZIP
gearbeitet werden sollte.

Das finale Laufzeit-Gate auf dem Zielsystem beziehungsweise in CI bleibt:

```bash
sh scripts/check.sh
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Die lokale Prüfung deckt Syntax, fachliche Rechenlogik, reale SQLite-Migration,
Datenerhalt, zentrale Frontend-Logik, Versionskonsistenz sowie Paket- und
Manifestintegrität ab. Ein vollständiger Container-Build mit den festgelegten
Lockfile-Abhängigkeiten bleibt davon getrennt.
