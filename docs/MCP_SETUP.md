# DocOfHome MCP einrichten (Verweis)

Die vollständige und maßgebliche MCP-Anleitung ist seit 1.7.7 in das bestehende
**DocOfHome-Handbuch/Runbook** integriert. In der Anwendung führt der Button
**„MCP-Dokumentation im Handbuch öffnen“** direkt zum Abschnitt „MCP-Zugriff und SWAG“.

Die folgende ältere Kurzfassung bleibt als Kompatibilitätsverweis erhalten.

DocOfHome 1.7.6 enthält den MCP-Server direkt im vorhandenen Backend. Es wird kein
zusätzlicher Docker-Container und kein zusätzlicher veröffentlichter Container-Port benötigt.

## 1. MCP in DocOfHome aktivieren

1. **Einstellungen → Integrationen → ChatGPT / MCP** öffnen.
2. **Token erzeugen** wählen und den angezeigten Token sofort sicher kopieren.
   DocOfHome speichert nur den SHA-256-Hash; der Klartext kann später nicht erneut angezeigt werden.
3. Eine Berechtigungsstufe auswählen:
   - **Nur lesen**: Abfragen ohne Änderungen.
   - **Lesen & Schreiben**: Abfragen, Bezugsobjekte/Tätigkeiten anlegen oder bearbeiten und Durchführungen protokollieren.
   - **Vollzugriff**: zusätzlich Löschoperationen.
4. Optional die öffentliche Adresse eintragen, zum Beispiel
   `https://mcp.example.de/mcp`.
5. **MCP-Zugriff aktivieren** und die Einstellungen speichern.

Der MCP-Endpunkt ist immer exakt `/mcp`. Die normale REST-API bleibt unter `/api/v1`.

## 2. Empfohlene Veröffentlichung über SWAG/nginx

Nach außen sollte ausschließlich der MCP-Endpunkt veröffentlicht werden. Die normale
DocOfHome-Oberfläche, `/api/v1` und `/docs` müssen für ChatGPT nicht erreichbar sein.

Beispiel für einen eigenen MCP-Hostnamen:

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name mcp.example.de;

    include /config/nginx/ssl.conf;

    location = /mcp {
        include /config/nginx/proxy.conf;
        proxy_pass http://docofhome:8000/mcp;
    }

    location / {
        return 404;
    }
}
```

`docofhome:8000` muss an den tatsächlichen internen Container-/Servicenamen angepasst
werden. Falls SWAG und DocOfHome nicht im selben Docker-Netz liegen, ist stattdessen ein
von SWAG erreichbares internes Ziel zu verwenden.

Am Router ist dafür kein zusätzlicher DocOfHome-Port erforderlich: Die externe Verbindung
läuft wie andere SWAG-Dienste über HTTPS/443.

## 3. MCP-Client verbinden

Im MCP-Client werden benötigt:

- URL: `https://mcp.example.de/mcp`
- Authentifizierung: Bearer Token
- Token: der einmalig von DocOfHome erzeugte Wert `doh_mcp_...`

Der HTTP-Header lautet technisch:

```text
Authorization: Bearer doh_mcp_...
```

## Sicherheitshinweise

- MCP ist nach einer Neuinstallation standardmäßig deaktiviert.
- Ohne eingerichteten Token lässt sich MCP nicht aktivieren.
- Ein deaktivierter MCP-Endpunkt antwortet mit HTTP 404.
- Ein fehlender oder falscher Token antwortet mit HTTP 401.
- **Token erneuern** invalidiert den bisherigen Token sofort.
- Der Token sollte nicht in Compose-Dateien, Git-Repositories oder öffentlich zugänglichen
  Reverse-Proxy-Konfigurationen hinterlegt werden.
- Für den normalen Einsatz mit ChatGPT ist **Lesen & Schreiben** sinnvoll; Vollzugriff sollte
  nur aktiviert werden, wenn MCP auch löschen dürfen soll.
