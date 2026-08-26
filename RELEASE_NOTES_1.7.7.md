# DocOfHome 1.7.7

Version 1.7.7 ergänzt ein strukturiertes Kochbuch, zentrale Modul- und
Navigationssteuerung, installierbare PWA-Unterstützung sowie die vollständige
MCP-/SWAG-Betriebsdokumentation im vorhandenen Handbuch und Runbook.

## Daten und Migration

- Migration `0052` legt die eigenständige Tabelle `recipes` an.
- Die vorhandene Modulauswahl wird um getrennte Hauptmenü-Sichtbarkeit ergänzt.
- Deaktivieren oder Ausblenden eines Moduls löscht keine Fachdaten.

## Bewusste Einschränkung

Eine gemeinsame Einkaufsliste ist noch nicht Bestandteil von 1.7.7. Sie wird als
spätere Erweiterung vorgesehen, weil Zusammenführung, Einheitenumrechnung,
Abhaken und mehrere Listen ein eigenes Datenmodell benötigen. Rezepte und Zutaten
sind bereits so strukturiert, dass diese Funktion später ohne Freitextmigration folgt.
