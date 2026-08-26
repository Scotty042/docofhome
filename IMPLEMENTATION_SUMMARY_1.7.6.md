# Implementation Summary 1.7.6

DocOfHome 1.7.6 integriert einen MCP-Server in das bestehende FastAPI-Backend.

## Architektur

- Offizielles MCP Python SDK 2.x (`mcp>=2.0,<2.1`)
- Streamable HTTP, stateless und JSON-Antworten
- exakte ASGI-Route im bestehenden FastAPI-Prozess unter `/mcp`
- gemeinsamer Lifecycle über den vorhandenen FastAPI-Lifespan
- fachliche MCP-Tools verwenden direkt dieselben DocOfHome-Services wie die REST-API

## Persistente Konfiguration

Die bestehende Tabelle `system_settings` speichert:

- `mcp.enabled`
- `mcp.permission`
- `mcp.public_url`
- `mcp.token_sha256` (Secret)

Dadurch ist keine Schemaänderung erforderlich und die bestehende Backup-/Exportlogik erfasst die Konfiguration automatisch.

## Authentifizierung

Ein reines ASGI-Middleware schützt den MCP-Mount mit Bearer-Authentifizierung. Der Token wird mit `secrets.token_urlsafe(32)` erzeugt; gespeichert wird nur sein SHA-256-Digest. Der Vergleich erfolgt konstantzeitnah mit `hmac.compare_digest`.

## Rechte

- `read`: ausschließlich lesende MCP-Tools
- `write`: lesen, erstellen, bearbeiten und Durchführungen protokollieren
- `admin`: zusätzlich Löschoperationen

Die Berechtigung wird nicht nur am HTTP-Zugang, sondern vor jedem fachlichen MCP-Tool erneut aus der persistenten Einstellung geprüft.
