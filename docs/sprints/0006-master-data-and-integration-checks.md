# Sprint 0006: Stammdaten und Integrationstests

## Ziel

Tectoryn soll nach der Ersteinrichtung ohne manuelle API-Aufrufe benutzbar sein. Nutzer können die für Assets erforderlichen Stammdaten im Web verwalten und gespeicherte optionale Integrationen sicher prüfen.

## Umfang

### Stammdaten

- eigener Navigationspunkt `Stammdaten`
- Reiter für Asset-Typen, Produkte und Labels
- Anlegen und Bearbeiten über validierte Webformulare
- Soft-Archivierung statt physischem Löschen
- optionales Einblenden archivierter Datensätze
- vollständige Seitennachladung ohne feste 100-Datensatz-Grenze
- bewusster Button zum Anlegen empfohlener Asset-Typen
- keine versteckten Seed-Daten
- direkter Verweis aus der Asset-Erfassung, wenn noch kein Asset-Typ existiert

### Integrationstests

- Home Assistant: authentifizierter Lesezugriff auf `/api/config`
- Immich: Prüfung des API-Keys und Lesen der Serverversion
- Nextcloud: schreibfreies `PROPFIND` auf den WebDAV-Benutzerpfad
- aktuelle Formulareingaben werden vor dem Test gespeichert
- Ergebnisse enthalten Status, verständliche Meldung, optionale Version und Antwortzeit
- Secrets und externe Antwortinhalte werden nie zurückgegeben
- fünf Sekunden Timeout
- keine automatischen HTTP-Weiterleitungen, damit Zugangsdaten nicht an andere Hosts weitergegeben werden

## Nicht enthalten

- keine Datenbankmigration
- kein physisches Löschen oder Wiederherstellen archivierter Stammdaten
- keine Synchronisation externer Daten
- kein Schreiben nach Home Assistant, Immich oder Nextcloud
- keine automatische Aktivierung empfohlener Asset-Typen

## Akzeptanzkriterien

- Ein Nutzer kann mindestens einen Asset-Typ vollständig im Web anlegen und anschließend ein Asset erfassen.
- Produkte können optional einem Asset-Typ zugeordnet werden.
- Labels können mit einer gültigen Hex-Farbe verwaltet werden.
- Bereits verwendete Datensätze werden nur archiviert; historische Beziehungen bleiben erhalten.
- Jeder Integrationstest verwendet ausschließlich serverseitig gespeicherte Zugangsdaten.
- Ungültige Zugangsdaten, falsche Endpunkte, Umleitungen, Timeouts und nicht erreichbare Server liefern verständliche, secret-freie Ergebnisse.
- Backend, Frontend, Migrationstest und Docker-Produktionsbuild bestehen.

## Validierung

- `ruff check app tests`
- `mypy app`
- `python -m pytest -q`
- frische Alembic-Migration bis `head`
- `npm test`
- `npm run build`
- Docker-Produktionsimage
