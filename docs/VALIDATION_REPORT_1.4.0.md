# Validierungsbericht DocOfHome 1.4.0

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.3.2  
Zielversion: DocOfHome 1.4.0  
Alembic-Head: `0034`

## 1. Umgesetzter Umfang

- Sammelschienen als passive Schrankkomponenten mit TE-Spanne, auswählbaren
  Außenleitern und Startphase;
- wiederholte Phasenfolge anhand der Position, beispielsweise
  `L1 – L2 – L3 – L1`;
- Zuordnung einer Sammelschiene zu einem FI/RCD;
- Zuordnung einer N-Schiene zu einem FI/RCD;
- automatische Ermittlung der wirksamen FI-Gruppe, N-Schiene und Phase eines
  Schutzgeräts unter einer Sammelschiene;
- manuelle Zuordnung mit Warnung bei abweichender oder unvollständiger
  Dokumentation;
- Sammelschiene als nicht platzverbrauchendes Overlay unter Schutzgeräten;
- optimierte Verteilungsansicht mit TE-Belegung, Kompakt-/Erweitert-Modus,
  Gruppeninformationen, Warnungen und Detailpanel;
- neue Migration `0034_home_electrical_groups`.

Der Umfang bleibt bewusst auf eine verständliche private Hausdokumentation
begrenzt. Einzelne Klemmen, Zähne oder Neutralleiteranschlüsse werden nicht
verwaltet.

## 2. Erfolgreich ausgeführte Prüfungen

Folgende Prüfungen wurden in der Arbeitsumgebung tatsächlich ausgeführt:

- Python-Syntaxprüfung für Backend, Migrationen, Tests und Skripte mit
  `python -m compileall`;
- Versionskonsistenz über `VERSION`, Backend, Frontend und Lockdatei;
- statische Releaseverträge für die Releases 1.2.4 bis 1.4.0;
- isolierte Migrationsprüfungen für `0030`, `0031`, `0032`, `0033` und `0034`;
- Migration `0034`: Upgrade, Downgrade und erneutes Upgrade auf einer
  repräsentativen SQLite-Datenbank;
- Pydantic-Validierung für eine dreiphasige Sammelschiene und eine reine
  N-Schiene;
- TypeScript-Syntaxprüfung der geänderten Frontend-Dateien über
  `typescript.transpileModule`;
- strukturelle Prüfung des Vue-Templates auf ausgeglichene Tags;
- ZIP-Roundtrip mit Größen- und SHA-256-Prüfung sämtlicher Manifestdateien
  nach der finalen Paketierung.

Zusätzlich wurden Regressionstests in den Quellstand aufgenommen für:

- die wiederholte Phasenfolge einer Sammelschiene;
- eine vom FI gespeiste Sammelschiene mit automatisch zugeordneter N-Schiene;
- Upgrade und Downgrade der Migration `0034`.

## 3. Nicht vollständig ausführbare Prüfungen

### Frontend

`npm ci` konnte in der Arbeitsumgebung nicht abgeschlossen werden, weil die
Paketquelle nicht zuverlässig erreichbar war. Deshalb werden Vitest,
`vue-tsc --noEmit` und der vollständige Vite-Build nicht als bestanden
behauptet. Die geänderten TypeScript-Quellen wurden syntaktisch geprüft, dies
ersetzt den vollständigen Frontend-Build jedoch nicht.

### Backend

Das erforderliche Paket `sqlmodel` war in der Arbeitsumgebung nicht installiert
und konnte von der verfügbaren Paketquelle nicht bezogen werden. Deshalb wurden
der vollständige Pytest-, Ruff- und mypy-Lauf nicht als bestanden gewertet.
Python-Syntax, Pydantic-Schemata und die eigenständige Alembic-/SQLAlchemy-
Migrationsprüfung wurden tatsächlich ausgeführt.

### Docker

Docker oder Podman steht in der Arbeitsumgebung nicht zur Verfügung. Image-Build,
Containerstart, Healthcheck und praktische Browserprüfung müssen auf dem
Zielsystem erfolgen.

## 4. Empfohlene Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach prüfen:

1. Alembic aktualisiert ohne Fehler auf Head `0034`.
2. Eine vorhandene Verteilung öffnet weiterhin ohne Datenverlust.
3. Ein FI/RCD lässt sich einer Sammelschiene und einer N-Schiene zuordnen.
4. Die Sammelschiene kann dieselben TE wie die zugehörigen Sicherungen
   überlagern.
5. Bei Startphase `L1` werden die Gerätepositionen wiederholend als
   `L1, L2, L3, L1 ...` angezeigt.
6. Beim Verschieben einer Sicherung wird die wirksame Phase neu berechnet.
7. FI und N-Schiene erscheinen am Schutzgerät und im Detailpanel.
8. Eine N-Schiene eines anderen FI erzeugt eine sichtbare Warnung.
9. Schutzgeräte und normale DIN-Assets lassen sich per Drag-and-drop sowie über
   den Positionierungsdialog verschieben.
10. Bestehende Mehrfacheinspeisungen, Verkabelungen und Verbrauchsdaten bleiben
    erhalten.

## 5. Bewertung

Der Sprintumfang ist im Quellstand umgesetzt und die neue Datenmigration wurde
isoliert erfolgreich geprüft. Die endgültige produktive Freigabe bleibt vom
vollständigen Frontend-/Backend-/Docker-Lauf und der praktischen Prüfung auf dem
Zielsystem abhängig.
