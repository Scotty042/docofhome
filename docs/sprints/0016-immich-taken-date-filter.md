# Sprint 0016 – Immich-Aufnahmedatumfilter

## Status

Implementiert auf `feature/immich-date-filter`; UI-Freigabe folgt in einem getrennten Sprint.

## Ziel

Die zentrale, schreibgeschützte Immich-Galerie erhält eine belastbare serverseitige Grundlage zur Einschränkung nach Aufnahmezeitraum. Trefferzahl und Pagination müssen aus Immich stammen und dürfen nicht nur die bereits geladene Seite filtern.

## Umfang

- optionale API-Parameter `taken_after` und `taken_before`
- Weitergabe an den stabilen Immich-Endpunkt `POST /search/metadata`
- Kombination mit Dateinamensuche, Album-ID und Favoritenfilter
- Prüfung, dass der Startzeitpunkt vor dem Endzeitpunkt liegt
- keine Datenbankmigration und keine lokale Speicherung der Filter
- Connector-Regressionstests für Payload und unverändertes Verhalten ohne Datumsfilter

## Sicherheitsgrenze

- ausschließlich lesende Immich-Berechtigung `asset.read`
- keine Änderungen, Uploads, Löschungen, Originaldownloads oder Albumaktionen
- API-Key und interne Immich-URL verbleiben im Backend
- externe Fehlerantworten werden nicht an den Browser durchgereicht

## Abnahme

- gültige Zeiträume werden als ISO-8601 an Immich weitergegeben
- ungültige oder leere Zeiträume erzeugen keine widersprüchliche Suche
- bestehende Suche ohne Datum bleibt kompatibel
- Standard-CI für Backend, Frontend, Migrationen und Docker ist grün
