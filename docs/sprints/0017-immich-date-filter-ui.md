# Sprint 0017 – Immich-Datumsfilter in der Galerie

## Status

Implementiert auf `feature/immich-date-filter-ui`. Der zugrunde liegende Backend-Vertrag aus Sprint 0016 ist mit Ruff, Mypy, Pytest, Alembic und Docker-Build vollständig validiert.

## Ziel

Die in Sprint 0016 eingeführten serverseitigen Aufnahmezeitraumfilter werden in der zentralen Bildergalerie sicher und responsiv bedienbar. Die Filterung bleibt vollständig serverseitig, damit Trefferzahl und Pagination korrekt bleiben.

## Umfang

- Datumsfelder **Aufgenommen ab** und **Aufgenommen bis**
- inklusive Filterung des vollständigen Endtages
- Kombination mit Dateinamensuche und Immich-Favoriten
- verständliche clientseitige Prüfung vertauschter Datumsgrenzen
- gemeinsames Zurücksetzen aller Galeriefilter
- typisierte API-Parameter `taken_after` und `taken_before`
- Regressionstest für die lokale API-Serialisierung

## Sicherheitsgrenze

- kein direkter Browserzugriff auf Immich
- kein API-Key und keine interne Immich-URL im Frontend
- keine Uploads, Änderungen, Löschungen, Favoriten- oder Albumaktionen
- keine Originaldownloads; die Vorschau verwendet weiterhin den geschützten Thumbnail-Proxy
- keine Datenbankmigration und keine persistierten Filter

## Abnahme

- einzelne oder kombinierte Datumsgrenzen können angewendet werden
- ein Enddatum umfasst den vollständigen ausgewählten Kalendertag
- ein Startdatum nach dem Enddatum verhindert die Anfrage und zeigt einen verständlichen Hinweis
- Suche, Favoritenfilter und Pagination bleiben kombinierbar
- Frontend-, Backend-, Migrations- und Docker-CI sind grün
