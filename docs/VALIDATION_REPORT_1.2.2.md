# Validierungsbericht DocOfHome 1.2.2

Stand: 24.07.2026  
Ausgangsbasis: DocOfHome 1.2.1  
Alembic-Head: `0029`

## Anlass

Der Docker-/Frontend-Build von 1.2.1 brach in
`frontend/scripts/check-mdi-icons.mjs` ab, weil
`mdi-label-plus-outline` in der festgeschriebenen Abhängigkeit `@mdi/font`
7.4.47 nicht enthalten ist.

## Änderung

In `frontend/src/pages/AssetEditorPage.vue` wurden beide Vorkommen durch
`mdi-tag-plus-outline` ersetzt. Backend, API, Modelle und Migrationen wurden
nicht verändert.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Suche nach `mdi-label-plus-outline` im Releasequellstand | Bestanden; kein Vorkommen mehr |
| Kontrolle beider Label-Aktionen auf `mdi-tag-plus-outline` | Bestanden; zwei Vorkommen |
| Abgleich mit der Iconliste von `@mdi/font` 7.4.47 | Bestanden; `mdi-tag-plus-outline` ist enthalten |
| `python3 scripts/check-version.py` | Bestanden; alle Versionsquellen `1.2.2` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 -m compileall -q backend/app backend/tests scripts` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| lokale Markdown-Linkprüfung | Bestanden |
| Scan auf Caches, lokale Datenbanken und Secrets | Bestanden |
| Manifestprüfung nach erneutem Entpacken | Bestanden |

## Nicht vollständig ausführbare Prüfungen

In der isolierten Releaseumgebung fehlen die vollständigen installierten npm-
und Python-Abhängigkeiten sowie Docker. Deshalb werden `npm ci`, `npm run build`,
Vitest, vollständiges Pytest, Ruff, mypy und Docker-Build hier nicht als
bestanden ausgewiesen. Der vom Betreiber gemeldete Buildabbruch liegt jedoch vor
dem TypeScript-/Vite-Schritt und wurde direkt an der vom Prüfer beanstandeten
Iconreferenz korrigiert.

## Datenbank und Migration

1.2.2 enthält keine neue Migration. Alembic-Head bleibt `0029`; ein neuer
Migrations-Roundtrip ist für diesen reinen Frontend-Patch nicht erforderlich.

## Empfohlene Zielsystemprüfung

1. `docker compose build --no-cache`;
2. prüfen, dass die MDI-Prüfung alle Icons als verfügbar meldet;
3. Container starten und Asset-Editor öffnen;
4. Inline-Labeldialog öffnen und ein Testlabel anlegen;
5. danach die üblichen Backend-, Frontend- und Smoke-Tests ausführen.

## Gesamturteil

Der konkrete MDI-Buildfehler aus 1.2.1 ist im Quellstand von 1.2.2 korrigiert.
API, Datenmodell und Migrationen bleiben unverändert. Die vollständige
Zielsystemprüfung muss im Docker-/CI-System mit installierten Abhängigkeiten
erfolgen.
