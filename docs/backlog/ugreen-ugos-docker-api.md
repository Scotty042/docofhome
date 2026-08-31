# Zukunftskandidat: UGREEN UGOS Docker-API-Anbindung

Stand: 28. August 2026
Status: Zurückgestellt / nicht implementiert

## Ziel

DocOfHome soll künftig Docker-Projekte und Container eines UGREEN-NAS read-only
über die interne UGOS-HTTPS-API einlesen können. Die Funktion ist bewusst
zurückgestellt, weil die sichere Berechtigungs- und Authentifizierungsstrategie
noch nicht abschließend geklärt ist.

## Bisher geprüfte Zugriffswege

- Docker Socket (`/var/run/docker.sock`): auf dem getesteten UGOS-System nicht
  praktikabel, weil der UGOS-Dateiauswahldialog keinen Zugriff auf `/var/run`
  ermöglicht.
- SSH: technisch möglich, aber aus Sicherheitsgründen für DocOfHome derzeit
  nicht gewünscht.
- Home Assistant: die vorhandene UGREEN-Integration liefert NAS-Sensorik, aber
  keine Docker-/Container-Entitäten.
- Direkte UGOS-HTTPS-API: technisch am vielversprechendsten und mit realen
  Antworten des NAS verifiziert.

## Verifizierte UGOS-Docker-Endpunkte

### `GetProjectListV3`

Liefert die logische Projekt-/Compose-Struktur, unter anderem:

- Projektname
- Pfad zur `docker-compose.yaml`
- Projektstatus
- Erstellungszeit
- Anzahl Container / laufende Container
- Containername
- Container-ID
- Kennzeichnung einer UGOS-Anwendung
- Felder für Image/Version/Restart-Policy sind vorhanden, waren im getesteten
  Projektlisten-Response jedoch leer.

Die Container-ID eignet sich als stabile externe Zuordnungs-ID.

### `POST /ugreen/v1/docker/container/ShowContainerDetailListV2`

Verifizierter Request-Body für eine vollständige Liste:

```json
{
  "name": "",
  "containerFilter": {
    "containerStatus": [],
    "containerType": [],
    "containerHasUp": []
  },
  "containerSort": {
    "containerSortEnum": 1,
    "containerSortOrder": 0
  },
  "pageNum": 1,
  "pageSize": 999999
}
```

Liefert pro Container unter anderem:

- `containerId`
- `status` (`running`, `exited`, ...)
- CPU- und RAM-Nutzung
- Gesamt-/RAM-Limit
- Upstream-/Downstream-Traffic
- Restart-Zustand
- erreichbare NAS-URLs
- Volume-Mappings inkl. `rw`/`ro`
- Port-Mappings
- Image-Update-Status

Dieser Endpunkt ist für einen regelmäßigen Bulk-Sync geeignet.

### `GET /ugreen/v1/docker/container/ShowLocalContainer?containerId=...`

Liefert detaillierte Containerdaten, unter anderem:

- Containername und Container-ID
- Status, Erstellungszeit und Laufzeit-/Health-Text
- Image-ID, Image-Name und Tag/Version
- Projektname
- Volumes und Ports
- Netzwerke inkl. Netzwerkname, Typ, interner IP und MAC-Adresse
- Container-Aliase/Links
- Restart-Einstellung
- CPU/RAM
- Hardwarebeschleunigung/GPU
- Prozessliste
- Environment-Variablen

WICHTIG: Environment-Variablen können Passwörter, API-Schlüssel und andere
Secrets enthalten. DocOfHome darf dieses Feld bei einer späteren Implementierung
nicht persistieren, nicht an das Frontend weitergeben und nicht protokollieren.
Auch Prozesslisten sind für den geplanten Anwendungsfall zunächst nicht nötig.

### `ShowOfflineContainer`

Der getestete Endpunkt liefert nur einen kleinen Status-/Ressourcendatensatz
(Container-ID/-Name, CPU, RAM, Traffic, Erstellungszeit). Er liefert auch für
laufende Container Daten und ist für die geplante Synchronisierung nicht nötig.

### `GetUpdateContainerCount`

Der getestete Response enthielt `result: 0`. Aufgrund des Namens und des Feldes
`imgHasUpdate` in den Containerdaten wird angenommen, dass dies die Anzahl der
Container mit verfügbarem Image-Update ist. Nicht als Änderungszähler für die
Containerliste verwenden, solange dies nicht ausdrücklich verifiziert ist.

## Geplantes Datenmodell / Zusammenführung

Empfohlene Hierarchie:

`UGREEN NAS -> Docker-Projekt -> Container -> Live-/Detaildaten`

Zusammenführung über `containerId`:

1. `GetProjectListV3`: Projekte, Container-Namen und Projektzuordnung.
2. `ShowContainerDetailListV2`: schneller regelmäßiger Status-/Ressourcen-Sync.
3. `ShowLocalContainer`: Detailimport bzw. gezielte Aktualisierung von Image,
   Netzwerken, Health und weiteren nicht-sensiblen Metadaten.

Manuell in DocOfHome gepflegte Metadaten müssen getrennt von Live-Daten bleiben.
Ein vorübergehend nicht erreichbarer Container/NAS darf nicht automatisch
als gelöscht behandelt werden; letzter bekannter Zustand und letzter Fehler
sollen sichtbar bleiben.

## Authentifizierung und Berechtigungen

Die UGOS-Weboberfläche verwendet authentifizierte Sessions/Tokens. Für eine
spätere Implementierung ist ein serverseitiger Login-Adapter vorgesehen, der
UGOS-Anmeldedaten ausschließlich im Backend verarbeitet und einen temporären
Session-/API-Token verwaltet bzw. erneuert.

Die konkrete Login-Sequenz und das Token-Lebenszyklusverhalten müssen vor der
Implementierung nochmals gegen die dann eingesetzte UGOS-Version verifiziert
werden. Interne/undokumentierte UGOS-Endpunkte können sich durch Firmware-Updates
ändern.

Ein eigens angelegter Nicht-Admin-Testbenutzer hatte in der UGOS-Weboberfläche
keinen Zugriff auf die Docker-App. Damit ist derzeit wahrscheinlich, dass Docker
Adminrechte benötigt. Ob die drei benötigten read-only API-Endpunkte direkt mit
einem eingeschränkten Benutzer aufrufbar wären, wurde noch nicht abschließend
verifiziert. Genau diese Berechtigungsfrage ist der Hauptgrund für das
Zurückstellen.

## Sicherheitsanforderungen für eine spätere Umsetzung

- eigener dedizierter UGOS-Benutzer, wenn möglich mit minimalen Rechten;
- ausschließlich read-only Docker-Endpunkte implementieren;
- keine Start/Stop/Restart/Delete/Update-Aktionen in der ersten Version;
- Zugangsdaten ausschließlich serverseitig und verschlüsselt speichern;
- Session-/API-Token nicht an das Frontend ausgeben;
- Tokens, Cookies und Credentials aus Logs redigieren;
- `environmentVariable` und andere secret-trächtige Felder sofort verwerfen;
- HTTPS-Verifikation nicht stillschweigend deaktivieren; bei lokalem/self-signed
  Zertifikat bevorzugt Zertifikats-/Fingerprint-Pinning oder explizite,
  sichtbar gekennzeichnete Ausnahme;
- Requests ausschließlich an den konfigurierten NAS-Host zulassen;
- Timeouts und Fehlerzustände sauber behandeln;
- bei API-Änderungen keine Daten löschen, sondern Integration als fehlerhaft
  markieren und letzten bekannten Stand behalten.

## Vorgesehene Bedienung in DocOfHome

Mögliche Integrationsfelder:

- Verbindungstyp: `UGREEN UGOS API`
- Host/IP
- Port (typisch 9443 beim getesteten System)
- HTTPS
- Benutzername
- Passwort
- Sync-Intervall: deaktiviert / 30 s / 1 min / 5 min / 15 min / 30 min
- `Verbindung testen`
- `Jetzt aktualisieren`
- letzter erfolgreicher Sync
- letzter Fehler

## Offene Punkte vor Umsetzung

1. Authentifizierungsablauf und Token-Erneuerung gegen aktuelle UGOS-Version
   vollständig verifizieren.
2. Prüfen, ob ein eingeschränkter Benutzer die benötigten read-only Endpunkte
   direkt aufrufen kann, auch wenn die Docker-App in der Weboberfläche fehlt.
3. Falls Adminrechte zwingend sind: Sicherheitsentscheidung treffen, ob ein
   dedizierter Admin-Account für diese Integration akzeptabel ist.
4. Verhalten bei abgelaufenen Sessions, NAS-Neustart und Firmware-Update testen.
5. Optional prüfen, ob weitere stabile Endpunkte für Health oder Image-Updates
   einen Mehrwert bieten.

