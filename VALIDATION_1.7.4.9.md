# Validierung DocOfHome 1.7.4.9

Stand: 24.08.2026

## Abgedeckte Verträge

- Versionskonsistenz `1.7.4.9` in VERSION, Backend, Frontend, Lockfile und SOURCE_INFO;
- Alembic-Head `0050`;
- allgemeine Bezugsobjekte einschließlich Typ `animal`;
- optionale `subject_id` an Work Items ohne Entfernung bestehender Zielverknüpfungen;
- rückwirkende Durchführungen über `occurred_at`;
- automatische Historie beim Erledigen;
- Intervallstatistik mit letztem, durchschnittlichem, kürzestem und längstem Abstand;
- Notiz, Kosten und Mess-/Zählerwert je Durchführung;
- DB-basierte Anhänge mit 20-MB-Grenze;
- Portabilität der Bezugsobjekte und Work-Item-Zuordnung;
- Regressionstest für `Penny → Impfung` mit 366 Tagen Abstand zwischen 03.02.2025 und 04.02.2026.

## In dieser Arbeitsumgebung ausgeführt

- Python-Syntaxprüfung der geänderten Backend-, API-, Modell-, Schema-, Service- und Migrationsdateien: erfolgreich;
- echter SQLite/Alembic-Test der Migration `0049 → 0050 → 0049`, einschließlich Backfill von `occurred_at` und BLOB-Anhang: erfolgreich;
- Pydantic-Vertragsprüfung für Bezugsobjekte, Kosten/Messwerte und Zuordnungsvalidierung: erfolgreich;
- dependency-freier Releasevertrag `scripts/check-release-1.7.4.9.py`: erfolgreich;
- dependency-freier TypeScript-Syntaxcheck über das vorhandene Projektskript: erfolgreich, sofern keine npm-Modulauflösung benötigt wird;
- JSON-Prüfung von SOURCE_INFO, package.json und package-lock.json: erfolgreich;
- finale Paketprüfung auf Version, Migrations-Head und erforderliche Dateien: erfolgreich vor Auslieferung.

## In dieser Arbeitsumgebung nicht vollständig ausführbar

- vollständiger Backend-Pytest sowie Ruff/mypy, da `sqlmodel` und weitere Projektabhängigkeiten nicht vollständig vorinstalliert sind; der direkte Alembic/SQLite-Migrationstest für `0050` wurde dagegen erfolgreich ausgeführt;
- Vue-Typecheck, Vitest und Vite-Build, da `frontend/node_modules` nicht im Quell-ZIP enthalten ist und der benötigte npm-Cache unvollständig ist. Ein Offline-Installationsversuch meldete fehlende Cache-Artefakte.

Die entsprechenden Projekt- und Regressionstests wurden im Quellstand ergänzt und sind für die normale CI-/Entwicklungsumgebung vorgesehen.
