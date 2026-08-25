# Validierung DocOfHome 1.7.5

Stand: 25.08.2026

## Erfolgreich

- Releasevertrag 1.7.5 und Versionskonsistenz
- Python-3.12-Kompilierung aller Backend- und Migrationsmodule
- Alembic-Neuaufbau von 0001 bis 0051 auf SQLite
- neue Backendtests für Wiederholung ohne Starttermin, Folgetermin und Datumssortierung: 2/2
- Vue-/TypeScript-Typprüfung
- Vite-Produktionsbuild (765 Module)
- Frontendtests: 170/175 erfolgreich

## Bestehende Regressionen aus der Basis 1.7.4.9

Fünf textbasierte Frontend-Vertragstests zu Elektroansicht und globalen Meldungen erwarten
ältere Quelltextfragmente, die im bereitgestellten 1.7.4.9-Stand bereits nicht mehr vorhanden
sind. Sie betreffen keine Datei der Bezugsobjekt-/Tätigkeiten-Änderung. Ein vorhandener
zeitabhängiger Backendtest zur Reaktivierung monatlicher Zähleraufgaben schlug ebenfalls fehl;
die neuen 1.7.5-Tests und die Migration sind davon unabhängig erfolgreich.

## Datenverträglichkeit

- Migration 0050 bleibt unverändert erhalten.
- Migration 0051 entfernt keine Tabellen oder Historieneinträge.
- Zweistellig gespeicherte Jahre werden von 00–99 in den Bereich 2000–2099 korrigiert.
- Wiederholungen ohne ersten Fälligkeitstermin sind nach der Migration zulässig.
