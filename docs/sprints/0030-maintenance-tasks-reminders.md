# Sprint 0030 – Wartungen, Aufgaben und Erinnerungen

- Status: Implemented locally; operator acceptance pending
- Target branch: `feature/maintenance-tasks`
- Depends on: Sprint 0029, ADR-0025

## Ziel

Einmalige Aufgaben und wiederkehrende Wartungen werden mit Fälligkeit, Priorität und Historie
verwaltet. Überfällige sowie bald fällige Einträge sind auf einer zentralen Seite und im Dashboard
sichtbar.

## Anforderungen

- Typen `task` und `maintenance`, Status `open`, `completed`, `cancelled`.
- Optionale Zuordnung zu denselben fünf lokalen Zieltypen wie Notizen und Dokumente.
- Wiederholung in Tagen nur für Wartungen mit Fälligkeit.
- Abschluss einer wiederkehrenden Wartung erzeugt einen Historieneintrag und verschiebt die nächste
  Fälligkeit in die Zukunft, statt den Plan zu schließen.
- Einmalige Aufgaben werden beim Abschluss als erledigt markiert.
- Erinnerungen bleiben in dieser Stufe anwendungsintern; keine E-Mail oder Push-Nachricht.

## Backend

- Tabellen `work_items` und `work_item_events` aus Migration `0020`.
- CRUD-, Abschluss-, Abbruch-, Wiederöffnungs-, Historien- und Summary-Endpunkte unter
  `/api/v1/work-items`.
- Zielobjekte werden serverseitig validiert; archivierte Objekte erhalten keine neuen Einträge.

## Frontend

- Zentrale responsive Seite `/maintenance` mit Status-/Typfilter, Kennzahlen und Editor.
- Wiederverwendbare Karte in Asset-, Raum- und Elektrodetailansichten.
- Dashboard zeigt offene und überfällige Einträge.

## Migrationen

- Additive Revision `0020` nach `0019`.
- Modulschlüssel `maintenance` wird vorhandenen Installationen additiv hinzugefügt.

## Tests

- Wiederkehrende Fälligkeit wird nach Abschluss in die Zukunft verschoben.
- Einmalige Aufgabe wird abgeschlossen; Historie und Summary bleiben konsistent.
- Validierung von Zielpaar, Wiederholung und Statusübergängen.

## Definition of Done

- [x] Datenmodell, API, Seite, Detailkarten und Dashboard umgesetzt.
- [x] Abschluss- und Wiederholungslogik mit Historie umgesetzt.
- [x] Migration und Tests ergänzt.
- [ ] Vollständige Docker- und Betreiberabnahme im Zielsystem.

## Nicht Bestandteil

- E-Mail, Push, Kalender-Synchronisation, Cron-Ausführung externer Aktionen oder automatische
  Arbeitsaufträge.
