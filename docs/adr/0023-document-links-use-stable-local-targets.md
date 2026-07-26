# ADR-0023: Dokumentverknüpfungen verwenden lokale Zielreferenzen und Nextcloud-Pfade

## Status

Accepted

## Entscheidung

Verknüpfungen werden lokal in `document_links` gespeichert. Jedes Linkobjekt enthält einen festen
Zieltyp, die lokale UUID des Ziels sowie den relativen Pfad, Namen und optionalen ETag-Snapshot des
verwalteten Nextcloud-Dokuments. Ein Dokument darf mit mehreren Fachobjekten verknüpft sein.

Beim Öffnen wird ausschließlich die bestehende geschützte Download-API verwendet. Zugangsdaten und
WebDAV-Adressen bleiben serverseitig. Wird eine Datei außerhalb von docofhome verschoben oder gelöscht,
bleibt die lokale Verknüpfung sichtbar und wird als nicht verfügbar gekennzeichnet; docofhome versucht
keine unsichere automatische Neuzuordnung anhand des Dateinamens.

Archivierte Fachobjekte behalten ihre Links lesbar, erhalten aber keine neuen Links.
