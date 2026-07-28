# DocOfHome 1.6.3.6 – Validierungsbericht

Stand: 28.07.2026

## Gemeldeter Fehler

Beim Anlegen eines Assets mit dem Asset-Typ **Smartes Relais / DIN-Schaltaktor**
und dem Produkt **Shelly Pro 1** antwortete die API mit HTTP 500.

## Ursache

Migration `0038_release_1_6_1_corrections` legte den Asset-Typ mit dem
Codepräfix `SRA` und das Produkt an, erzeugte jedoch keinen zugehörigen Eintrag
in `asset_code_counters`. Die Codevergabe verwendete bei der ersten Erfassung
ein `UPDATE ... RETURNING` und erwartete zwingend einen vorhandenen Zähler.
Ohne Datensatz endete `scalar_one()` mit einer unbehandelten Ausnahme.

## Korrekturen

- Migration `0046_repair_asset_code_counters` ergänzt fehlende Zähler für alle
  Asset-Typen.
- Vorhandene, aber zu niedrige Zähler werden auf die höchste vergebene Nummer
  plus eins angehoben.
- Bestehende `jarvis_code`-Werte werden nicht verändert.
- Die Laufzeit-Codevergabe verwendet `scalar_one_or_none()` und rekonstruiert
  einen fehlenden Zähler selbstheilend aus vorhandenen Codes.
- Ein Backend-Regressionstest bildet einen fehlenden `SRA`-Zähler mit bereits
  vorhandenem `SRA-007` ab und erwartet anschließend `SRA-008` und `SRA-009`.

## Ausgeführte Prüfungen

- Versionskonsistenz `1.6.3.6`: bestanden
- Releasevertrag `1.6.3.6`: bestanden
- Branding und gesammelte Korrekturverträge: bestanden
- Elektro- und Kammschienenverträge: bestanden
- Python-Syntax für Backend, Migrationen, Tests und Prüfscripte: bestanden
- Syntax von 181 TypeScript-/Vue-Skripteinheiten: bestanden
- alle vorhandenen Migrationsprüfungen `0030` bis `0046`: bestanden
- Migration `0046`: fehlender Zähler, veralteter Zähler und Idempotenz geprüft

## Nicht in dieser Umgebung ausführbar

- vollständige Pytest-Suite, da `sqlmodel` nicht installiert ist
- Ruff und Mypy mit den Projektabhängigkeiten
- `npm test` und `npm run build`, da `node_modules` nicht vorhanden ist
- Docker-Build, da Docker in der Build-Umgebung nicht verfügbar ist

Diese Einschränkungen betreffen nicht die erfolgreich ausgeführte isolierte
SQLite-Migrationsprüfung und die statischen/Syntaxprüfungen der Korrektur.
