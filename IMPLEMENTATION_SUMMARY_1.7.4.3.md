# Implementation Summary 1.7.4.3

## Ausgangslage

Die schematische Feldrandführung aus 1.7.4.2 führte sämtliche feldübergreifenden
Leitungen über obere Korridore. Bei langen oder unterhalb liegenden Zielgeräten
konnten Wege dadurch abgeschnitten werden oder vollständig aus dem sichtbaren
Bereich verschwinden.

## Umsetzung

- Routing wieder auf frei innerhalb der Schrankfläche verlaufende orthogonale
  Pfade umgestellt.
- Leiterabstand wird nicht nur an den Endpunkten, sondern auch auf horizontalen
  und vertikalen Trassen berücksichtigt.
- Mehrere Verbindungen an einem Endpunkt werden anhand der Gegenposition
  sortiert und auf separate Anschlussports verteilt.
- Verbindungswege erhalten begrenzte Spurversätze, ohne an Feldränder gezwungen
  zu werden.
- Stromkreis-, MCB- und RCBO-Zweige bleiben aus der Hauptansicht entfernt.
- Keine Schemaänderung; Alembic-Head `0049`.
