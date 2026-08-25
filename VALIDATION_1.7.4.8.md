# Validierung DocOfHome 1.7.4.8

Stand: 24.08.2026

## Abgedeckte Regressionen

- Monate mit 31 und 30 Tagen;
- Februar mit 28 Tagen und Schaltjahr mit 29 Tagen;
- zu frühe Ablesung am Monatsanfang;
- Ablesung am Beginn des gültigen Fensters;
- Ablesung exakt am Fälligkeitstag;
- verspätete Ablesung nach Monatswechsel;
- offene überfällige Aufgabe ohne gültige Ablesung;
- zusätzliche Erinnerungstage als Kalendertage;
- identische Kernlogik in Reminder-API und automatischem Aufgabengenerator.

## Ausgeführte Prüfungen

- Versionskonsistenz (`VERSION`, Backend, Frontend und Lockfile): erfolgreich;
- Releasevertrag `scripts/check-release-1.7.4.8.py`: erfolgreich;
- Branding- und gesammelte Releaseverträge: erfolgreich;
- JSON-Syntax von `SOURCE_INFO.json`, `package.json` und `package-lock.json`:
  erfolgreich;
- AST-Syntaxprüfung aller geänderten Python-Module und Tests: erfolgreich;
- dependency-freier Lauf der gemeinsamen Kalenderlogik für 31/30 Tage,
  Februar, Schaltjahr, frühe, fristgerechte und verspätete Ablesung sowie
  zusätzliche Kalendertage: erfolgreich;
- statische Prüfung, dass der letzte Migrationsstand `0049` ist: erfolgreich;
- finales ZIP erneut entpackt, Dateiliste und Dateiinhalte mit dem Paketstand
  verglichen: vor Bereitstellung erfolgreich durchgeführt.

## In dieser Umgebung nicht ausführbar

- vollständige Python-/Backend-Tests, Ruff und mypy;
- Alembic-Upgrade, Alembic-Check und ausführbare Migrationstests;
- Vitest, Vue-/TypeScript-Typprüfung und npm-Build.

Die bereitgestellte Umgebung enthält nur Apple Python 3.9 ohne pytest,
SQLModel, SQLAlchemy, Alembic, Pydantic, Ruff oder mypy. Das Projekt setzt
Python 3.13 voraus. Node und npm sowie `frontend/node_modules` sind ebenfalls
nicht vorhanden. Es wurden keine externen Pakete nachgeladen; alle lokal
möglichen Prüfungen wurden ausgeführt.

## Migration

Keine Schemaänderung. Der neueste Migrationsstand bleibt `0049`.
