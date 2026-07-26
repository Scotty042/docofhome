# Sprint 0029 – Wiki und Notizen

- Status: Implemented locally; operator acceptance pending
- Target branch: `feature/wiki-and-notes`
- Depends on: Sprint 0028, ADR-0024

> Dieser Vertrag ergänzt die verbindlichen Regeln aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

Hauswissen wird in hierarchischen Wiki-Seiten dauerhaft gespeichert. Zusätzlich können freie
Notizen direkt an Assets, Bereiche/Räume, Verteilungen, Schutzgeräte und Stromkreise angehängt
werden.

## Anforderungen

- Wiki-Seiten besitzen stabile UUIDs, Titel, global eindeutigen Slug, Inhalt und optionalen
  Elternknoten.
- Seiten können gesucht, hierarchisch angezeigt, bearbeitet und archiviert werden.
- Zyklen sowie das Archivieren einer Seite mit aktiven Unterseiten werden verhindert.
- Notizen sind einem festen lokalen Zielobjekt zugeordnet und werden soft gelöscht.
- Archivierte Zielobjekte zeigen vorhandene Notizen schreibgeschützt.
- Wiki-Titel und -Inhalte werden in die globale Suche aufgenommen.

## Backend

- Tabellen `wiki_pages` und `domain_notes` aus Migration `0019`.
- API unter `/api/v1/wiki/pages` und `/api/v1/notes`.
- Zielprüfung verwendet die bestehenden lokalen UUIDs und akzeptiert keine freien Zieltypen.
- Slugs werden serverseitig normalisiert und kollisionsfrei vergeben.

## Frontend

- Responsives Wiki unter `/wiki` mit Suche, Hierarchie, Detailansicht und Editor.
- Wiederverwendbare Notizkarte in den fünf bestehenden Detailkontexten.
- Verständliche Lade-, Leer-, Validierungs- und Fehlerzustände.

## Migrationen

- Additive Revision `0019` nach `0018`.
- Keine bestehenden Datensätze oder technischen Legacy-Bezeichner werden verändert.

## Tests

- Wiki-Hierarchie, Suche, Zyklenschutz und Archivgrenzen.
- Notiz-CRUD, Zielvalidierung und Soft Delete.
- Globale Suche liefert die feste zusätzliche Gruppe `wiki_page`.

## Definition of Done

- [x] Datenmodell, API und Oberfläche umgesetzt.
- [x] Wiki in die globale Suche integriert.
- [x] Notizen in alle unterstützten Detailansichten integriert.
- [x] Migration und Regressionstests ergänzt.
- [ ] Vollständige Docker- und Betreiberabnahme im Zielsystem.

## Nicht Bestandteil

- Mehrbenutzerrechte, Rich-Text-WYSIWYG, Dateianhänge im Editor oder öffentliche Freigabelinks.
- Fälligkeiten und Wiederholungen; diese gehören zu Sprint 0030.
