# Sprint 0031 – Dokumentationsqualität

- Status: Implemented locally; operator acceptance pending
- Target branch: `feature/documentation-quality`
- Depends on: Sprint 0030, ADR-0026

## Ziel

docofhome erkennt fehlende Kerndaten, nicht verfügbare Dokumentverknüpfungen, leere Wiki-Seiten
und überfällige Arbeiten, ohne Benutzerdaten automatisch zu verändern.

## Anforderungen

- Persistenter Qualitätslauf mit Punktwert 0–100 und den Schweregraden Fehler, Warnung, Hinweis.
- Manuelle Prüfung über die Oberfläche und automatische Prüfung höchstens einmal innerhalb von 24
  Stunden durch den bestehenden leichtgewichtigen Hintergrundbetrieb.
- Prüfungen für fehlende Asset-Orte/Beschreibungen/Kennungen, schwach dokumentierte Bereiche,
  unvollständige Stromkreise, leere Wiki-Seiten, überfällige Arbeiten und nicht verfügbare
  Dokumentlinks.
- Jeder Hinweis besitzt nachvollziehbaren Code, Beschreibung und – sofern sicher – eine lokale Route.
- Prüfungen sind ausschließlich beratend und ändern niemals Fachdaten.

## Backend

- Tabellen `quality_runs` und `quality_issues` aus Migration `0021`.
- API `/api/v1/quality/latest` und `/api/v1/quality/run`.
- Maximal 30 Qualitätsläufe werden aufbewahrt.
- Nextcloud-Dateiprüfung erfolgt nur bei aktivierter Integration und ausschließlich über den
  vorhandenen serverseitigen Dokumentendienst.

## Frontend

- Responsive Seite `/quality` mit Punktwert, Zählern und Filtern.
- Direkte lokale Navigation zu betroffenen Datensätzen.
- Dashboard zeigt Qualitätswert und Anzahl der Hinweise.

## Migrationen

- Additive Revision `0021` nach `0020`.
- Modulschlüssel `quality` wird vorhandenen Installationen additiv hinzugefügt.

## Tests

- Bericht erkennt fehlende Assetdaten, leere Wiki-Seite und überfällige Aufgabe.
- Punktwert und Schweregrad-Zähler sind deterministisch.
- Der zuletzt abgeschlossene Lauf bleibt abrufbar.

## Definition of Done

- [x] Qualitätsmodell, Prüfdienst, Scheduler, API und Oberfläche umgesetzt.
- [x] Dashboard-Integration und lokale Zielrouten umgesetzt.
- [x] Migration und Tests ergänzt.
- [ ] Vollständige Docker-, Nextcloud- und Betreiberabnahme im Zielsystem.

## Nicht Bestandteil

- Automatische Korrekturen, KI-generierte Inhalte, Norm- oder Sicherheitszertifizierung sowie
  Benachrichtigungen außerhalb der Anwendung.
