# DocOfHome – aktueller Status und Backlog

Stand: 17. November 2026 · Release: 1.11.0 · Alembic-Head: `0063`

Ticketbasierte Zeiterfassung mit Start, Pause, Ende, Wiederaufnahme sowie Ticket- und Tagessummen. Das Handbuch, zehn MCP-Werkzeuge und JSON-/CSV-Export sind ergänzt. Vollständige Backups enthalten die neue Tabelle.

Aktueller Stand und Prüfgrenzen: `../PROJECT_STATUS.md`, `../PROJECT_HISTORY.md` und `../AUDIT.md`. Historische Release-Unterlagen stehen gebündelt in `../PROJECT_HISTORY.md`.

Verlauf mit Standard letzte 30 Tage, Schnellauswahl und Von/Bis. Manuelle Arbeitsläufe und nachträgliche Zeitkorrekturen mit erlaubten Überschneidungen sind umgesetzt. Noch nicht umgesetzt: Benutzerzuordnung und Datenimport von Arbeitsläufen. Produktive Installation und GitHub-Veröffentlichung sind nicht Teil des lokalen Paketbaus.

Tagesgruppen mit Datum und Tagessumme; kompakte Eingabe von Tätigkeit/Ticketnr und Kunde. Wiederaufnahmeliste auf heute beschränkt.

Arbeitsläufe können nach Bestätigung gelöscht werden. Ein zusätzlicher MCP-Löschzugriff benötigt admin; insgesamt 59 Werkzeuge.

Ende leert die drei Eingabefelder nach erfolgreicher Speicherung; bei Pause oder Speicherfehler bleiben sie erhalten.

Neu: sortierbare Spalten innerhalb der Tage, optionale Kundengruppierung, Kundenname in den Tätigkeitssummen und gespeicherte BCS-Markierung pro Arbeitslauf.

Monatlicher CSV-Export mit eigener Aktivierung, optionalem Nextcloud-Ziel und Downloads. Vollständige Backups sichern Exportkonfiguration und CSVs. Authentik wird separat eingerichtet; vorbereitete SWAG-Vorlagen und Compose-Alternative liegen unter deploy/swag und compose.swag.yaml. Gruppierung als Checkbox und Spaltenkopf einmal pro Tag.
