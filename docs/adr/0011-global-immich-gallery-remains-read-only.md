# ADR-0011: Die globale Immich-Galerie bleibt schreibgeschützt

## Status

Angenommen

## Kontext

docofhome benötigt neben objektbezogenen Fotoverknüpfungen eine zentrale Bilderansicht. Immich ist jedoch das führende System für Bilddateien, Metadaten, Alben und Lebenszyklus. Eine direkte Browseranbindung würde den API-Key oder die private Immich-Adresse offenlegen und die bisherige Sicherheitsgrenze durchbrechen.

## Entscheidung

Die globale Galerie verwendet ausschließlich die vorhandenen docofhome-Backend-Endpunkte für Suche und Vorschaubilder.

- Der Browser spricht nur mit `/api/v1/immich`.
- Der API-Key verbleibt serverseitig.
- Vorschaubilder laufen durch den begrenzten, validierenden Thumbnail-Proxy.
- Die Galerie ist rein lesend.
- Such- und Pagingzustand werden nicht dauerhaft gespeichert.
- Ein Ausfall von Immich verändert keine lokal gespeicherten Asset-Verknüpfungen.

## Folgen

### Positiv

- einheitliche Sicherheitsgrenze für Asset-Galerie und globale Galerie
- kein zusätzlicher Datenbank- oder Migrationsbedarf
- keine Bildduplikate in docofhome
- große Bibliotheken bleiben durch Pagination beherrschbar
- die Darstellung kann später domänenübergreifend wiederverwendet werden

### Negativ

- ohne Immich-Verbindung können in der globalen Galerie keine Vorschaubilder geladen werden
- Album-, Datum- und Favoritenfilter sind noch nicht verfügbar
- Bildbearbeitung bleibt bewusst ausschließlich in Immich

## Nicht entschieden

Die spätere Verknüpfung von Immich-Bildern mit Räumen, Verteilungen oder Dokumentationsobjekten benötigt ein separates, typisiertes Linkmodell und eine eigene additive Migration.
