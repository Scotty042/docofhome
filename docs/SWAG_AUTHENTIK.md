# DocOfHome hinter SWAG und Authentik (optional, ab 1.11.0)

Diese Version bereitet die Anbindung vor. Sie installiert keinen Authentik-Container und aktiviert keine öffentliche Freigabe. Authentik wird separat eingerichtet und kann anschließend auch andere Anwendungen schützen. Die normale lokale Installation funktioniert weiter wie bisher.

## Zielbild und Grenzen

Browser → HTTPS/SWAG → Authentik-Anmeldeprüfung → DocOfHome. Der gesamte Browserbereich einschließlich API, Downloads und Einstellungen benötigt eine gültige Authentik-Sitzung. Der Proxy erlaubt den Zugriff nur nach erfolgreicher Prüfung; ein nicht erreichbarer Authentik-Dienst gewährt keinen anonymen Durchlass.

DocOfHome selbst besitzt weiterhin keine Benutzertrennung. Alle in Authentik zugelassenen Benutzer arbeiten mit derselben Instanz und denselben Daten und App-Funktionen. Authentik-Gruppen sind Zugangsbeschränkungen, keine DocOfHome-Rollen. Keine ungeprüften Benutzer für diese Anwendung freischalten. Identitätsheader von Clients sind keine App-Anmeldung. Die Templates erzeugen keine lokalen DocOfHome-Benutzer oder OAuth-Sitzungen.

## Abstimmung mit der separaten Authentik-Einrichtung

Für diese Vorlage werden benötigt:

- Eine stabile öffentliche Authentik-Adresse, beispielsweise https://auth.example.com, mit HTTPS.
- Eine eigene DocOfHome-Adresse, beispielsweise https://docofhome.example.com.
- Aktuelle, gepflegte SWAG- und Authentik-Versionen. Insbesondere bekannte nginx-Forward-Auth-Sicherheitskorrekturen müssen installiert sein; alte Outpost-Images mit aktualisieren.
- In Authentik eine Application mit Proxy Provider im Modus **Forward auth (single application)**, External host exakt die öffentliche DocOfHome-Adresse; Application dem eingebetteten oder separaten Proxy-Outpost zuordnen.
- Zugriff an eine ausdrücklich zugelassene Benutzergruppe binden. Ein verpflichtender Authentik-Anmeldeflow mit MFA ist im separaten Authentik-Chat einzurichten: zum Beispiel Passwort plus TOTP oder WebAuthn/Passkey mit passender Benutzerverifikation. Registrierung eines Geräts allein erzwingt MFA noch nicht. Wiederherstellungszugang/Notfallcodes vor Freigabe testen.
- SWAG, DocOfHome und der Outpost müssen sich auf dem gewählten Docker-Proxy-Netz erreichen. Die Vorlage erwartet den Outpost als `authentik-server:9000`; bei einem separaten Outpost dessen Containeralias einsetzen. Dieses Netz und Authentik selbst werden hier nicht erstellt.

## Dateien und Aktivierung

- `compose.swag.yaml`: **vollständige Alternative** zur normalen Compose-Datei, kein Merge-Override. Keine `ports`-Freigabe für DocOfHome, nur interner Port 8000. Das bestehende `./data` bleibt eingebunden.
- `deploy/swag/docofhome.subdomain.conf.sample`: Browser-VHost mit Authentik-Prüfung.
- `deploy/swag/docofhome-mcp.subdomain.conf.sample`: optionaler separater MCP-VHost.

Vor Änderungen vollständiges Backup erstellen. Im **bestehenden Installationsverzeichnis** arbeiten, damit `./data` und `.env` erhalten bleiben. `SWAG_NETWORK` in der bestehenden `.env` auf das bereits eingerichtete externe Proxy-Netz setzen (Standard: `proxy`). Die alternative Compose-Datei nicht zusätzlich mit `-f compose.yaml` kombinieren: Ein Merge könnte die alte Portfreigabe erhalten.

Nach Abstimmung mit der anderen Authentik-Einrichtung:

1. In der Browser-Vorlage **alle** Vorkommen von `docofhome.example.com` ersetzen. `authentik-server` auf den tatsächlichen Outpost-Alias anpassen. Keine Zugangsdaten oder Tokens in diese Dateien schreiben.
2. Datei als `/config/nginx/proxy-confs/docofhome.subdomain.conf` im bestehenden SWAG-Konfigurationsvolume ablegen. DNS und gültiges HTTPS-Zertifikat müssen zu dieser Adresse passen. Authentiks eigene öffentliche Domain erhält ihre separat eingerichtete SWAG-Konfiguration.
3. Im alten DocOfHome-Projekt zunächst die bisherige Instanz kontrolliert stoppen, ohne Datenvolumes zu entfernen:

   ```sh
   docker compose -f compose.yaml down
   docker compose -f compose.swag.yaml up -d --build
   ```

   Falls bisher andere Dateinamen oder ein expliziter Projektname verwendet wurden, diese beibehalten. Nicht parallel eine alte Instanz mit offenem Port weiterlaufen lassen. Das neue Template bindet den Docker-Socket absichtlich nicht ein; für Docker-Überwachung ist die vorhandene SSH-Anbindung vorgesehen. Ein bewusst benötigter lokaler Socket wäre separat privilegiert einzurichten.
4. Konfiguration prüfen und erst bei Erfolg neu laden:

   ```sh
   docker exec swag nginx -t
   docker exec swag nginx -s reload
   ```

   Den SWAG-Containernamen ggf. ersetzen. Bei fehlgeschlagenem Test nicht neu laden.
5. Nur SWAG/HTTPS über den Router freigeben; keinen direkten DocOfHome-Port 8088 oder 8000. Die Compose-Alternative veröffentlicht keinen solchen Host-Port. Prüfen, ob alte Container, zusätzliche Portfreigaben oder andere Proxy-VHosts einen Zugang an Authentik vorbei bieten.

Für Schreibzugriffe auf die App blockiert die Vorlage fremde Browser-Origins, auch von anderen Subdomains. Die Origin-Freigabe muss zur öffentlichen DocOfHome-HTTPS-Adresse passen. Die Auth-Prüfung erlaubt nur ausgewählte Header, setzt die ursprüngliche URL selbst und verwirft clientseitiges `X-Original-URI`. Outpost-Pfade werden ausschließlich an Authentik weitergeleitet; sie öffnen keinen ungeschützten Zugang zu DocOfHome. Die genaue interne Auth-Prüfadresse ist als `internal` markiert. Nicht durch `auth_request off`, `satisfy any` oder einen anonymen `/api`-VHost aufweichen.

## MCP bleibt ein eigener Zugangsweg

Die Browser-Vorlage liefert für `/mcp` und `/mcp/…` bewusst 404. Interaktive MFA eignet sich nicht für die bisherigen MCP-Tokenzugriffe. Bei Bedarf die separate MCP-Vorlage aktivieren:

- Alle Vorkommen von `mcp.example.com` ersetzen, HTTPS/DNS einrichten und die Datei als aktive `.conf` in SWAG ablegen.
- Nur `/mcp` und Unterpfade werden zu DocOfHome geleitet; alle anderen Pfade liefern 404. Weder Oberfläche noch normale `/api/v1`-Routen werden dadurch freigegeben.
- MCP muss in DocOfHome aktiviert sein und weiterhin einen gültigen eigenen Token verlangen. Bestehende read/write/admin-Rechte bleiben gültig. `Authorization: Bearer …` ist vorzuziehen; der bisherige Tokenpfad bleibt kompatibel. Request-Access-Logging ist im MCP-Location-Block ausgeschaltet, damit Tokenpfade dort nicht protokolliert werden.
- Als öffentliche MCP-Adresse in DocOfHome und im Client die separate Domain mit `/mcp` verwenden. Auf diesem VHost keine interaktive Authentik-Abfrage ergänzen, solange die Clients weiterhin DocOfHome-Bearer-Tokens nutzen.
- CSV- und Backup-Downloads bleiben auf der geschützten Browser-Domain. Ein MCP-Lesewerkzeug darf Dateien auflisten, erhält dadurch aber keinen anonymen Browser-Downloadzugang.

## Abnahmetests nach Einrichtung

In einem privaten Browser ohne Anmeldung müssen Oberfläche **und** `/api/v1/time-tracking` zur Authentik-Anmeldung führen. Direkte POST-/PUT-/DELETE-Anfragen ohne Sitzung dürfen keine App-Änderung ausführen. Benutzer ohne App-Zuweisung werden abgewiesen. Bei einem testweise nicht erreichbaren Outpost darf kein Zugriff auf App-Daten möglich sein.

Nach erfolgreicher Anmeldung den verpflichtenden MFA-Ablauf, Zeiterfassung, BCS, CSV-Download, Backup-Download und größere Uploads prüfen. Nach Logout erneut den privaten Zugriff prüfen. Ein in den Browser eingefügter `X-authentik-username`- oder `X-Original-URI`-Header darf keine Anmeldung ersetzen.

Beim optionalen MCP-VHost gilt: ohne Token 401, bei deaktiviertem MCP 404; mit gültigem Token tools/list und die erlaubten Werkzeuge prüfen. `/`, `/api/v1/backups` und andere App-Pfade müssen dort auch mit gültigem MCP-Token 404 liefern.

## Validierungsstand

Templates und Compose-Struktur werden lokal durch Konfigurationsverträge geprüft. In der Paketbau-Umgebung stehen weder Docker noch nginx zur Verfügung; es wird kein erfolgreich ausgeführtes `nginx -t` oder Ende-zu-Ende-Test mit dem zukünftigen Authentik-Dienst behauptet. Die oben genannten Tests sind nach dessen Einrichtung erforderlich, bevor die Anwendung öffentlich genutzt wird.

Offizielle Referenzen, geprüft am 17. November 2026: [Authentik Proxy Provider](https://docs.goauthentik.io/add-secure-apps/providers/proxy/), [nginx Forward Auth](https://docs.goauthentik.io/add-secure-apps/providers/proxy/server_nginx/), [SWAG](https://docs.linuxserver.io/images/docker-swag/), [Authentik nginx-Sicherheitskorrektur](https://docs.goauthentik.io/security/cves/GHSA-5wcc-hf24-rf5h/).
