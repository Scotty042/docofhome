# Sprint 0028 – Dokumentverknüpfungen

## Status

Implemented locally; operator acceptance pending

## Ziel

Verwaltete Nextcloud-Dateien können mit Assets, Bereichen/Räumen, Verteilungen, Schutzgeräten und
Stromkreisen verknüpft und aus deren Detailansichten wieder geöffnet werden.

## Lieferumfang

- additive Migration `0018` und Tabelle `document_links`
- feste Zieltypen `asset`, `location`, `distribution`, `protective_device`, `circuit`
- API zum Auflisten, Anlegen und Entfernen von Verknüpfungen
- serverseitige Prüfung von Zielobjekt und Nextcloud-Datei
- mehrfach verwendbare Dokumente, aber keine Duplikate je Zielobjekt
- lokale Namens- und ETag-Snapshots für nachvollziehbare Fehlerzustände
- wiederverwendbare responsive Dokumentenkarte mit geschütztem Dateibrowser
- schreibgeschützte Anzeige an archivierten Zielen
- keine Uploads im Verknüpfungsdialog; Dateiverwaltung bleibt im Dokumentenmodul

## Sicherheitsgrenzen

- keine Nextcloud-Zugangsdaten oder internen WebDAV-Adressen im Browser
- nur relative Pfade unterhalb des konfigurierten Dokumenten-Stammordners
- keine automatische Dateisuche nach Name bei externem Verschieben
- Entfernen eines Links löscht niemals die Nextcloud-Datei

## Abnahme

- ein Dokument kann mit jedem unterstützten Zieltyp verbunden werden
- dasselbe Dokument darf mit mehreren Zielobjekten verbunden sein
- derselbe Pfad kann nicht doppelt mit demselben Ziel verbunden werden
- externe Löschung oder Verschiebung wird als nicht verfügbar angezeigt
- archivierte Ziele zeigen bestehende Links, erlauben aber keine neuen
