# ADR 0006: Serverseitige, schreibfreie Integrationstests

## Status

Akzeptiert

## Kontext

Home Assistant, Immich und Nextcloud werden in Tectoryn mit URL und Secret konfiguriert. Ein Browser-Test würde Secrets erneut an den Client binden, CORS-Probleme erzeugen und interne Dienste unnötig direkt aus dem Browser ansprechen. Ein reiner Erreichbarkeitstest würde außerdem nicht bestätigen, dass die gespeicherten Zugangsdaten gültig sind.

## Entscheidung

Verbindungstests werden als synchroner Backend-Service ausgeführt. Der Browser übermittelt nur die Integrationsart. Das Backend liest die bereits gespeicherte Konfiguration und führt einen dienstspezifischen, schreibfreien Request aus:

- Home Assistant: `GET /api/config` mit Bearer-Token
- Immich: `GET /api-keys/me` und `GET /server/version` mit `x-api-key`
- Nextcloud: `PROPFIND` mit Tiefe 0 auf dem WebDAV-Benutzerpfad und Basic Auth

Vor dem Test speichert das Frontend die aktuellen Einstellungen über den bestehenden Settings-Endpunkt. Die Testantwort enthält nur Integrationsart, Erfolg, kontrollierte Meldung, optionale Version und Antwortzeit.

HTTP-Weiterleitungen werden nicht verfolgt. Requests haben ein festes Timeout von fünf Sekunden. TLS-Zertifikate werden regulär geprüft. Externe Antwortkörper, URLs, Tokens, API-Keys und Passwörter werden nicht an den Browser zurückgegeben oder protokolliert.

## Folgen

### Positiv

- Secrets bleiben serverseitig.
- CORS ist für die externen Dienste irrelevant.
- Die Prüfung bestätigt Authentifizierung und nicht nur Erreichbarkeit.
- Es werden keine externen Daten verändert.
- Fehlertexte bleiben verständlich und geben keine fremden Inhalte preis.

### Einschränkungen

- Selbstsignierte oder ungültige TLS-Zertifikate werden abgelehnt.
- Weiterleitende URLs müssen durch die direkte interne Zieladresse ersetzt werden.
- Nextcloud benötigt einen expliziten Benutzernamen beziehungsweise ein Konto.
- Ein Test ist eine Momentaufnahme und kein dauerhaftes Monitoring.
