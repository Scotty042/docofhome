# DocOfHome 1.0.0 – Validierungsbericht

Datum: 23. Juli 2026

## Backend

- FastAPI-Komplettimport: bestanden (`DocOfHome API`, Version `1.0.0`)
- Ruff: bestanden
- mypy: bestanden, 108 Quelldateien
- Pytest: bestanden, 189 Tests
- frische Datenbank: bestanden
- Alembic `upgrade head` und `check`: bestanden
- Upgrade 0023 → 0026: bestanden
- Wiederanlauf von 0024 mit verwaister `_alembic_tmp_work_items`-Tabelle:
  bestanden; kanonischer Datensatz erhalten, Arbeitstabelle entfernt und
  Revision 0026 erreicht
- Downgrade 0026 → 0023 → 0026: bestanden
- neue API-/Service-, Datenintegritäts- und Connector-Tests: bestanden

## Frontend

- finales `npm ci` mit `package-lock.json`: bestanden
- MDI-Prüfung: bestanden, 205 Icons
- Vitest: bestanden, 104 Tests in 32 Dateien
- `vue-tsc --noEmit`: bestanden
- Vite-Produktionsbuild: bestanden
- Branding-Prüfung: bestanden
- iPhone-typische Breite 390 × 844: bestanden; Ablesedialog füllt den
  Viewport, Zahlenfeld verwendet `type=number`, `inputmode=decimal` und den
  zählerabhängigen `step`
- direkter SPA-Aufruf `/consumption`: bestanden

Der Produktionsbuild meldet lediglich den nicht blockierenden Hinweis auf ein
JavaScript-Hauptbundle über 500 kB. Funktion, Cachebarkeit und Kompression sind
nicht beeinträchtigt.

## Container

- Compose-Struktur: bestanden
- Healthcheck vorhanden: bestanden
- kein privilegierter Modus und kein Docker-Socket: bestanden
- FastAPI-Importschritt im Dockerfile vorhanden: bestanden
- echter Image-Build/Container-Neustart: auf dem ausführenden Windows-Host nicht
  ausführbar, da weder Docker, Podman noch WSL installiert sind

Dieser Umgebungsstatus ist kein verschleierter Testerfolg. Der Dockerfile- und
Compose-Vertrag wurde statisch und der identische Startpfad lokal mit frischem
Datenordner, Migration, Readiness, direktem SPA-Aufruf und erneutem Start gegen
den persistenten Ordner geprüft.

## Datenintegrität und Sicherheit

- globale Inventarnummern einschließlich Archivreservierung: bestanden
- Kalenderregeln über Februar, Schaltjahr und Sommerzeitgrenze: bestanden
- Ableseerinnerung verschwindet nur nach Ablesung derselben Periode: bestanden
- fehlende Vergleichswerte bleiben `null`, keine falsche Null: bestanden
- Importvorschau ohne Write, Konfliktstrategien und Rollback: bestanden
- JSON-/CSV-Export ohne Integrations-URLs, Konten oder Secrets: bestanden
- Audit redigiert sensible Felder und ist unveränderlich: bestanden
- Archive, Dokumentlinks, Wiki-Restore, Suche, VLAN-null und Nextcloud-Ordner:
  vollständige Regression bestanden

## Release-Artefakt

Das Paket wird nach Erstellung in ein frisches Verzeichnis entpackt. Ausschlüsse,
Versionskonsistenz, FastAPI-Import, Frontendbuild und SHA-256 werden erneut
geprüft; das Ergebnis steht im externen Release-Manifest.
