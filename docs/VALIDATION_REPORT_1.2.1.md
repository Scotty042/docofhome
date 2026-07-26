# Validierungsbericht DocOfHome 1.2.1

Stand: 24.07.2026  
Ausgangsbasis: DocOfHome 1.2.0  
Alembic-Head: `0029`

## Umfang

DocOfHome 1.2.1 ist ein Dokumentations- und Statuspflege-Release. Es wurden
keine fachlichen Funktionen, API-Verträge, Migrationen oder produktiven
Quellcodedateien geändert. Angepasst wurden zentrale Versionsquellen sowie
Projekt-, Roadmap-, Sprint-, Release- und Qualitätsdokumentation.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| `python3 scripts/check-version.py` | Bestanden; alle Versionsquellen `1.2.1` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 -m compileall -q backend/app backend/tests scripts` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden; 10/10 Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| Vergleich mit dem entpackten 1.2.0-Quellstand | Nur freigegebene Dokumentations- und Versionsdateien verändert |
| Archivvergleich des alten Projektstatus | Original vollständig und bytegleich erhalten |
| Archivvergleich des frühen Audits | Original vollständig und bytegleich erhalten |
| lokale Markdown-Linkprüfung | Bestanden |
| Scan auf generierte Caches und lokale Secrets | Bestanden; keine Release-Reste gefunden |
| Manifestprüfung nach erneutem Entpacken | Bestanden |

## Nicht vollständig ausführbare Prüfungen

### Backend

`pytest` ist vorhanden, die Testsammlung bricht jedoch wegen der nicht
installierten Laufzeitabhängigkeit `sqlmodel` ab. `ruff` und `mypy` sind in der
Ausführungsumgebung nicht installiert. Es wird daher kein vollständiger
Backend-Testlauf als bestanden ausgewiesen.

### Frontend

Node.js 22 und npm 10 sind vorhanden, aber `node_modules` fehlt. Ein bewusst
offline ausgeführtes `npm ci --offline --ignore-scripts` scheitert, weil nicht
alle Pakete im lokalen Cache liegen. Vitest, `vue-tsc` und der Vite-Build konnten
daher nicht ausgeführt werden.

### Docker

Docker ist in der Ausführungsumgebung nicht installiert. Ein Image- und
Container-Smoke-Test war nicht möglich.

## Datenbank und Migration

1.2.1 enthält keine neue Migration. Alembic-Head bleibt `0029`. Die bereits für
1.2.0 dokumentierte Kette bis 0029 wird nicht durch dieses Patch-Release
verändert. Da keine Schema- oder Modelldateien geändert wurden, war kein neuer
Migrations-Roundtrip erforderlich.

## Dokumentationsbereinigung

Geprüft wurde insbesondere:

- `PROJECT_STATUS.md` benennt 1.2.1, Head 0029 und keinen aktiven Sprint;
- `docs/CURRENT_STATUS_AND_BACKLOG.md` ist die aktuelle Backlogquelle;
- `docs/SPRINT_REGISTER.md` trennt historische Verträge von aktuellen Sprints;
- Sprint 0039 ist `Draft / Planning only` und kein Implementierungsauftrag;
- der alte Status `0.1.18-dev` liegt vollständig unter `docs/archive`;
- der frühere Root-Audit liegt vollständig unter `docs/archive`;
- README, Roadmap, Changelog und Release Notes verweisen auf 1.2.1;
- historische Sprintverträge wurden nicht rückwirkend verändert.

## Empfohlene Zielsystemprüfung

Vor einem produktiven Einsatz von 1.2.x weiterhin durchführen:

1. vollständiges Backup des persistenten Datenordners;
2. `ruff`, `mypy` und vollständiges `pytest` in der Projektumgebung;
3. `npm ci`, Vitest, `vue-tsc` und Vite-Build;
4. Docker-Build und Containerstart;
5. Start mit einer Kopie der bestehenden Datenbank;
6. reale HA-Bedienprüfung mit mehreren Tausend Entitäten.

## Gesamturteil

Das Release ist als Dokumentations- und Statuspflegepaket konsistent. Die
historischen Inhalte bleiben erhalten, während der aktuelle Projektplan nun
eindeutig ist. Vollständige anwendungsbezogene Backend-, Frontend- und
Dockerprüfungen bleiben wegen fehlender lokaler Abhängigkeiten ein Zielsystem-
oder CI-Gate und werden nicht als bestanden behauptet.
