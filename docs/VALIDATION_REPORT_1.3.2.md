# Validierungsbericht DocOfHome 1.3.2

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.3.1-r2  
Zielversion: DocOfHome 1.3.2  
Alembic-Head: `0033`

## 1. Fehlerursache

Die Anwendung und die aktuellen Modelle erlaubten bereits mehrere eingehende
Verbindungen an einem Phasenverteilerblock. Auf bestehenden Installationen war
jedoch teilweise weiterhin der historische SQLite-Index
`uq_electrical_connections_active_target` vorhanden. Dieser Index erzwang trotz
Anwendungslogik genau eine aktive Quelle je Ziel.

Die Ursache lag darin, dass Migration `0027` auf der betroffenen Installation
bereits als ausgeführt markiert war. Eine nachträgliche Korrektur derselben
historischen Migrationsdatei wird von Alembic nicht erneut angewendet.

## 2. Umgesetzte Korrektur

- neue Migration `0033_remove_legacy_single_target_topology_index`;
- idempotente Prüfung, ob der historische Ziel-Unique-Index noch existiert;
- Entfernung ausschließlich dieses Indexes;
- keine Änderung oder Löschung bestehender Verbindungen;
- weiterhin eindeutige vollständige Verbindungspaare, damit dieselbe Quelle
  nicht doppelt mit demselben Ziel verbunden werden kann;
- deutsche und konkretere Datenbank-Konfliktmeldungen;
- Regressionstest für eine bereits bis `0032` migrierte Alt-Datenbank mit
  verbliebenem Ziel-Unique-Index.

## 3. Erfolgreich ausgeführte Prüfungen

- `python -m compileall -q backend/app backend/tests backend/migrations/versions scripts`
- `python scripts/check-version.py`
- `python scripts/check-branding.py`
- `python scripts/check-collected-fixes.py`
- `python scripts/check-reading-reminders.py`
- `python scripts/check-release-1.2.4.py`
- `python scripts/check-release-1.3.0.py`
- `python scripts/check-release-1.3.1.py`
- `python scripts/check-release-1.3.2.py`
- `python scripts/check-migration-0030.py`
- `python scripts/check-migration-0031.py`
- `python scripts/check-migration-0032.py`
- `python scripts/check-migration-0033.py`

Die isolierte Prüfung von Migration `0033` hat den historischen Index entfernt
und anschließend zwei unterschiedliche Quellen auf demselben
`cabinet_component`-Ziel erfolgreich gespeichert. Ein erneutes Upgrade blieb
idempotent.

## 4. Nicht vollständig ausführbare Prüfungen

### Frontend

`npm ci` konnte in der Arbeitsumgebung nicht abgeschlossen werden. Die
Paketquelle antwortete innerhalb des verfügbaren Zeitfensters nicht vollständig.
Daher wurden `vue-tsc --noEmit`, `vite build` und Vitest für diesen Stand nicht
als bestanden gewertet. An den Frontend-Quellen war für 1.3.2 keine funktionale
Änderung erforderlich.

### Backend

Das vollständige Backend-Paket `sqlmodel` war in der Umgebung nicht verfügbar
und konnte von der Paketquelle nicht installiert werden. Deshalb wurde der
komplette Pytest-Lauf nicht ausgeführt. Python-Syntax und die eigenständige
Alembic-/SQLAlchemy-Migrationsprüfung wurden tatsächlich ausgeführt.

### Docker

Docker oder Podman steht in der Arbeitsumgebung nicht zur Verfügung. Image-Build,
Containerstart, Healthcheck und praktische Browserprüfung müssen auf dem
Zielsystem erfolgen.

## 5. Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach prüfen:

1. Alembic-Head ist `0033` und es erscheint kein Migrationsfehler.
2. Eine vorhandene Einspeisung zum Phasenverteilerblock bleibt bestehen.
3. Eine zweite Quelle kann auf denselben Phasenverteilerblock gespeichert werden.
4. Beide Einspeisungen werden in der Versorgungstopologie angezeigt.
5. Eine identische Verbindung zwischen derselben Quelle und demselben Ziel wird
   weiterhin abgelehnt.
6. Phasenregeln bleiben aktiv: Ein ausschließlich mit L1 versorgter Block darf
   L2 nicht als Abgang ausgeben.

## 6. Bewertung

Die konkrete Ursache der gemeldeten Mehrfacheinspeisungsstörung ist mit einer
neuen, für Bestandsinstallationen wirksamen Migration korrigiert. Die
Paketfreigabe bleibt abhängig vom vollständigen Docker-Build und der praktischen
Prüfung auf dem Zielsystem.
