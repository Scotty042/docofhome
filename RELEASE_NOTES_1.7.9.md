# DocOfHome 1.7.9

Version 1.7.9 erweitert MCP auf die ersten drei priorisierten Fachgruppen. Alle Funktionen
aus 1.7.8 bleiben erhalten.

## Wissen und Kochbuch

- Rezepte suchen und vollständig lesen, anlegen, ändern und löschen
- Wiki-Seiten suchen, lesen, anlegen, ändern und archivieren
- verknüpfte Notizen lesen, anlegen, ändern und löschen

## Assets, Orte und Stammdaten

Der Katalogzugriff unterstützt `asset`, `location`, `asset_type`, `product` und `label`.
Für jeden Bereich stehen Suche, Detailansicht, Anlegen, Ändern und kontrolliertes Archivieren
zur Verfügung. Es gelten dieselben Referenz- und Konfliktprüfungen wie in der Weboberfläche.

## Verbrauch und Netzwerk

- Verbrauchszusammenfassung, Zähler und Ablesungen lesen
- Zähler und Ablesungen anlegen, ändern und archivieren
- Netzwerkgeräte, Segmente, Schnittstellen, Adressen und Verbindungen verwalten

## Berechtigungen

- `read`: Suche und Lesen
- `write`: Anlegen und Ändern
- `admin`: Löschen und Archivieren

Keine Datenbankmigration. Der Alembic-Head bleibt `0052`.
