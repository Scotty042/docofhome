# Sprint 0022 – Assets an Stromkreisen

## Status

Lokal implementiert und geprüft.

## Ziel

Ein dokumentierter Stromkreis zeigt die tatsächlich versorgten Geräte und sonstigen Assets. Die
Zuordnung verwendet ausschließlich bestehende Asset-Datensätze und erzeugt kein zweites Inventar.

## Umfang

- eigene responsive Detailansicht für Stromkreise
- serverseitig durchsuchbare und paginierte Auswahl aus allen aktiven Assets
- beliebig viele Asset-Zuordnungen pro Stromkreis
- direkte Navigation vom Stromkreis zum zugeordneten Asset
- Schutz vor doppelten aktiven Zuordnungen
- schreibgeschützter Erhalt der Zuordnung bei archivierten Stromkreisen oder Assets
- historisches Entfernen einer Zuordnung ohne Löschung des Assets
- additive Datenbankmigration `0015`

## Abgrenzung

- keine Leitungsberechnung, Selektivitätsprüfung oder automatische Elektroplanung
- keine weitere Immich-Funktion
- keine automatische Zuordnung anhand von Raum, Verteilung oder Asset-Typ

## Abnahme

- bestehende Assets lassen sich suchen, seitenweise anzeigen, zuordnen und wieder lösen
- doppelte Zuordnungen sowie neue Verbindungen zu archivierten Datensätzen werden abgewiesen
- archivierte Stromkreise bleiben mit ihren aktiven Zuordnungen lesbar
- Backend-, Frontend-, Migrations- und Produktions-Build-Prüfungen sind erfolgreich
