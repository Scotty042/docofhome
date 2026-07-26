# Validierungsbericht DocOfHome 1.2.3

Stand: 24.07.2026  
Ausgangsbasis: DocOfHome 1.2.2  
Alembic-Head: `0029`

## Anlass

Der Docker-/Frontend-Build von 1.2.2 bestand die MDI-Prüfung mit 218 Icons,
brach anschließend jedoch bei `vue-tsc --noEmit` ab. In
`frontend/src/services/immichGallery.test.ts` fehlte im Test-Fixture das
Pflichtfeld `online_product_image_search_enabled` aus `ConfigurationRead`.

## Änderung

- Das Test-Fixture enthält nun
  `online_product_image_search_enabled: false`.
- `selectedImmichAlbumId` akzeptiert nur noch
  `Pick<ConfigurationRead, 'integrations'>`, weil die Funktion ausschließlich
  die Integrationsliste benötigt.
- Backend, API, Datenmodell und Migrationen wurden nicht verändert.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| gezielte TypeScript-Prüfung mit globalem TypeScript 5.x für `settings.ts`, `immich.ts`, `immichGallery.ts` und `immichGallery.test.ts` | Bestanden |
| Kontrolle des Test-Fixtures auf `online_product_image_search_enabled` | Bestanden |
| Kontrolle des eingeschränkten Funktionsparameters auf `Pick<ConfigurationRead, 'integrations'>` | Bestanden |
| `python3 scripts/check-version.py` | Bestanden; alle Versionsquellen `1.2.3` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 -m compileall -q backend/app backend/tests scripts` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden; 10/10 Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| lokale Markdown-Linkprüfung | Bestanden |
| Scan auf Caches, lokale Datenbanken und typische Secret-Dateien | Bestanden |
| Manifestprüfung nach erneutem Entpacken | Bestanden |

## Vom Zielsystem bereits bestätigte Teilprüfung

Der vom Betreiber ausgeführte Docker-Build meldete vor dem TypeScript-Fehler:

```text
218 MDI-Icons geprüft: alle verfügbar.
```

Damit ist der vorherige MDI-Fehler aus 1.2.1/1.2.2 nicht erneut aufgetreten.

## Nicht vollständig ausführbare Prüfungen

### Vollständiger Frontend-Build

Ein erneutes `npm ci` in der isolierten Releaseumgebung scheiterte wiederholt am
internen npm-Paketdienst:

```text
HTTP 503 beim Abruf von why-is-node-running-2.3.0.tgz
```

Dadurch konnten `vitest`, `vue-tsc` über das echte Projekt-Node-Modul und
`vite build` hier nicht vollständig ausgeführt werden. Der konkret gemeldete
Typfehler wurde jedoch mit dem vorhandenen globalen TypeScript-Compiler gezielt
und erfolgreich geprüft.

### Vollständiger Backend-Test

`python3 -m pytest -q` konnte nicht starten, weil `sqlmodel` in der isolierten
Umgebung nicht installiert ist. Der Fehler lautet:

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

Docker ist in dieser Umgebung ebenfalls nicht verfügbar. Diese Prüfungen werden
nicht als bestanden ausgewiesen.

## Datenbank und Migration

1.2.3 enthält keine neue Migration. Alembic-Head bleibt `0029`; ein neuer
Migrations-Roundtrip ist für diesen reinen Frontend-Typprüfungsfix nicht
erforderlich.

## Empfohlene Zielsystemprüfung

1. `docker compose build --no-cache`;
2. prüfen, dass die MDI-Prüfung weiterhin 218 verfügbare Icons meldet;
3. prüfen, dass `vue-tsc --noEmit` den bisherigen Fehler in
   `immichGallery.test.ts` nicht mehr meldet;
4. Vite-Build vollständig bis zum Ende ausführen;
5. Container starten und Immich-Auswahl sowie Einstellungen öffnen;
6. anschließend die üblichen Backend-, Frontend- und Smoke-Tests ausführen.

## Gesamturteil

Der konkret gemeldete TypeScript-Buildfehler aus 1.2.2 ist im Quellstand von
1.2.3 korrigiert. Die Typabhängigkeit wurde zusätzlich fachlich eingegrenzt,
damit unabhängige Konfigurationserweiterungen diesen Test nicht erneut brechen.
API, Datenmodell und Migrationen bleiben unverändert. Die vollständige
Zielsystemprüfung muss im Docker-/CI-System mit installierten Abhängigkeiten
erfolgen.
