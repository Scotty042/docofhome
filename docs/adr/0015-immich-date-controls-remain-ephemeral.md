# ADR-0015 – Immich-Datumsfilter bleiben flüchtige Ansichtsparameter

## Status

Akzeptiert.

## Kontext

Die zentrale Immich-Galerie benötigt eine Einschränkung nach Aufnahmezeitraum. Eine lokale Speicherung der gewählten Filter oder eine nachträgliche clientseitige Filterung würde zusätzliche Zustände erzeugen und könnte bei paginierten Bibliotheken unvollständige Ergebnisse anzeigen.

## Entscheidung

Die Datumswerte werden ausschließlich als flüchtige Ansichtsparameter geführt und bei jeder Suche an die docofhome-API übergeben. Das Backend validiert den Zeitraum und reicht ihn an Immich weiter. Trefferzahl und Pagination stammen aus der serverseitig gefilterten Immich-Antwort.

Das Enddatum wird in der Oberfläche als einschließlich des vollständigen Kalendertages interpretiert. Die Auswahl wird nicht in SQLite, Browser-Speichern oder Immich persistiert.

## Folgen

- keine Datenbankmigration oder neue Persistenz
- korrekte Trefferzahlen auch bei großen Bibliotheken
- kombinierbar mit Dateinamensuche, Favoriten und späteren Albumfiltern
- erneutes Öffnen der Galerie beginnt bewusst ohne Datumsfilter
- Browser erhält weiterhin weder Immich-URL noch API-Key
