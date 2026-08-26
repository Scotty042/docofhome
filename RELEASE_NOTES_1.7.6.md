# DocOfHome 1.7.6

## Integrierter MCP-Zugang

- DocOfHome enthält jetzt einen eigenen MCP-Server direkt im bestehenden Backend und Docker-Image.
- Der Streamable-HTTP-Endpunkt liegt unter `/mcp`; ein zusätzlicher Container ist nicht erforderlich.
- MCP ist standardmäßig deaktiviert und wird vollständig unter **Einstellungen → Integrationen → ChatGPT / MCP** konfiguriert.
- Die öffentliche MCP-Adresse kann separat hinterlegt werden, zum Beispiel `https://mcp.example.de/mcp` für einen Reverse Proxy.

## Sicherheit

- Jeder MCP-Zugriff benötigt einen eigenen Bearer-Token.
- Tokens werden mit 256 Bit Zufall erzeugt und nur einmal im Klartext angezeigt.
- Persistiert wird ausschließlich der SHA-256-Hash des Tokens; normale API-Antworten enthalten niemals den gespeicherten Token.
- Berechtigungsstufen: **Nur lesen**, **Lesen & Schreiben** und **Vollzugriff**.
- Löschwerkzeuge stehen ausschließlich mit Vollzugriff zur Verfügung.
- Empfohlen bleibt, am Reverse Proxy extern nur `/mcp` freizugeben; Weboberfläche, REST-API und `/docs` müssen nicht öffentlich erreichbar sein.

## MCP-Werkzeuge

Lesend verfügbar sind unter anderem:

- DocOfHome-/Versionsinformationen
- Bezugsobjekte suchen
- Tätigkeiten suchen und einzeln lesen
- Tätigkeitshistorie lesen
- fällige und überfällige Tätigkeiten abfragen

Mit Schreibberechtigung zusätzlich:

- Bezugsobjekte anlegen und bearbeiten
- Tätigkeiten anlegen und bearbeiten
- Durchführung für heute oder ein angegebenes Datum protokollieren
- historische Durchführungen ergänzen

Mit Vollzugriff zusätzlich:

- Historieneinträge löschen
- Tätigkeiten löschen/archivieren
- unbenutzte Bezugsobjekte löschen

## Kompatibilität

- 1.7.6 basiert vollständig auf 1.7.5; Bezugsobjekte, Tätigkeiten und Historien bleiben unverändert erhalten.
- Es ist keine neue Datenbankmigration nötig. Die MCP-Konfiguration nutzt die bereits vorhandenen Systemeinstellungen; der Token selbst wird ausschließlich als SHA-256-Hash gespeichert.
- Alembic-Head bleibt `0051`.
