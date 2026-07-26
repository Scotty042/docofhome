# Sprint 0032 – Netzwerkmodul

- Status: Implemented locally; operator acceptance pending
- Target branch: `feature/network-module`
- Depends on: Sprint 0031, ADR-0027
- Package version: `0.1.17-dev`
- Migration head: `0022`

## Ziel

docofhome dokumentiert die lokale Netzwerkstruktur auf Basis der bereits vorhandenen Assets.
Netzwerkgeräte erhalten Schnittstellen, MAC- und IP-Adressen, IP-Netze mit vollständig optionaler
VLAN-ID sowie explizite physische, logische oder drahtlose Verbindungen. Es findet keine automatische
Netzwerkerkennung und keine Konfiguration externer Geräte statt.

## Verbindlicher Umfang

### Netzwerkgeräte

- Ein aktives Asset kann höchstens eine aktive Netzwerkrolle besitzen.
- Rollen: Router, Firewall, Switch, Access Point, Server, NAS, Client, IoT-Gerät, Drucker,
  Controller und Sonstiges.
- Netzwerkprofil mit Hostname, optionaler Management-URL und Netzwerknotizen.
- Asset bleibt die führende Identität für Name, Typ, Produkt, Raum, Bilder, Dokumente und Notizen.
- Eine aktive Netzwerkrolle blockiert Archivierung und Ersatz des zugrunde liegenden Assets.

### IP-Netze und optionale VLANs

- Name, CIDR, optionale VLAN-ID 1–4094, Gateway, DNS-Server und Beschreibung.
- Aktive Namen und VLAN-IDs sind eindeutig.
- Gateway und zugeordnete IP-Adressen müssen im konfigurierten Netz liegen.
- Ein Netz mit zugeordneten aktiven IP-Adressen kann nicht archiviert werden.

### Schnittstellen und Adressen

- Physische und virtuelle Schnittstellen mit Name, Typ, MAC-Adresse, Geschwindigkeit, PoE-Rolle,
  Aktivstatus und Beschreibung.
- Schnittstellennamen sind pro Gerät eindeutig; aktive MAC-Adressen sind global eindeutig.
- IPv4- und IPv6-Adressen mit Vergabeart, optionalem Netz, Hostname, Primärkennzeichnung und Notiz.
- Pro Netzwerkgerät kann höchstens eine Adresse als primär markiert sein.
- Archivierung einer Schnittstelle archiviert ihre Adressen und Verbindungen mit.

### Verbindungen und Topologie

- Zwei unterschiedliche Schnittstellen werden physisch, logisch oder drahtlos verbunden.
- Status: aktiv, geplant oder inaktiv; optional Kabeltyp, Kabelkennung und Beschreibung.
- Die Endpunkte werden kanonisch sortiert, sodass dieselbe Verbindung nicht in Gegenrichtung
  doppelt angelegt werden kann.
- Die Topologie ist eine aus den dokumentierten Verbindungen abgeleitete Übersicht und keine
  automatische Erkennung.

### Integration

- Responsive Hauptseite `/network` und Gerätedetail `/network/devices/{id}`.
- Direkte Anlage einer Netzwerkrolle aus einer Asset-Detailseite.
- Dashboard-Zusammenfassung.
- Globale Suche nach Assetname, docofhome-Code, Hostname, Rolle, Produkt, Raum, MAC-Adresse,
  IP-Adresse, Netz und VLAN.
- Dokumentationsqualität meldet fehlende Hostnamen, Schnittstellen und IP-Adressen beratend.
- Asset-Notizen und Nextcloud-Dokumentverknüpfungen werden über die bestehende Asset-Identität
  wiederverwendet.
- Home-Assistant-Geräte bleiben physische Asset-Bezüge; explizit zugeordnete Entitäten werden
  als aktuelle Eigenschaften am selben Asset angezeigt und nicht als zusätzliche Assets erzeugt.
- `Ctrl+K` fokussiert die globale Suche; archivierte Wiki-Seiten bleiben über das Archiv lesbar.

## Datenmodell und Migration

Migration `0022` ergänzt:

- `network_devices`
- `network_segments`
- `network_interfaces`
- `network_addresses`
- `network_connections`

Alle Datensätze verwenden UUIDs, Zeitstempel und Soft Delete. Eindeutigkeits- und Wertebereiche
werden zusätzlich durch SQLite-Constraints beziehungsweise partielle eindeutige Indizes geschützt.
Der Modulschlüssel `network` wird bestehenden Installationen additiv hinzugefügt.

## Sicherheit und Grenzen

- Management-URLs müssen HTTP(S)-URLs ohne eingebettete Zugangsdaten sein.
- Die Browseroberfläche spricht ausschließlich mit der lokalen `/api/v1/network`-API.
- Es werden keine Switches, Router, Firewalls oder Access Points abgefragt oder verändert.
- Keine Zugangsdaten, SNMP-Communitys, SSH-Schlüssel oder API-Tokens im Netzwerkmodell.
- Keine Portscans, automatische Discovery, Live-Statusprüfung oder Topologiebehauptungen.

## Automatisierte Tests

- Servicefluss für Geräte, Schnittstellen, Netze, Adressen, Verbindungen und Topologie.
- Konflikte für doppelte IP-Adressen und umgekehrte Doppelverbindungen.
- Subnetzvalidierung und kaskadierende Soft-Delete-Semantik.
- Asset-Lebenszyklus bleibt bei aktiver Netzwerkrolle geschützt.
- API-Komplettfluss und sichere HTTP-Fehlercodes.
- Migration `0021 → 0022 → 0021` einschließlich Tabellen und zentraler Indizes.
- Frontend-API-Client verwendet ausschließlich die lokale v1-API.
- Globale Suche deckt Netzwerkgruppen, IP-Adressen und optionale VLANs ab.
- Home-Assistant-Assetprojektion, archivierter Wiki-Zugriff und zugehörige API-Verträge sind durch
  Regressionstests ergänzt.

## Praktische Betreiberabnahme

1. Bestehendes Asset als Router oder Switch zum Netzwerkgerät machen.
2. Dasselbe Asset erneut zuordnen und den erwarteten Konflikt prüfen.
3. Netz `192.168.10.0/24` ohne VLAN-ID, aber mit optionalem Gateway und DNS anlegen.
4. Zwei Geräte mit Schnittstellen und unterschiedlich formatierten MAC-Adressen anlegen.
5. IP-Adresse innerhalb des Netzes anlegen; Adresse außerhalb des Netzes muss abgewiesen werden.
6. Zweite primäre IP am selben Gerät anlegen und prüfen, dass die bisherige Primärmarkierung entfällt.
7. Zwei Schnittstellen verbinden; umgekehrte Doppelverbindung muss abgewiesen werden.
8. Netzwerkübersicht, Gerätedetail und Topologie auf Desktop und Mobilgerät prüfen.
9. Globale Suche mit Hostname, MAC, IP und Netzname prüfen; VLAN-ID nur ergänzend testen, wenn sie genutzt wird.
10. Qualitätslauf starten und Hinweise für ein absichtlich unvollständiges Netzwerkgerät prüfen.
11. Archivierung von Asset und Netz bei aktiven Abhängigkeiten prüfen.
12. Home-Assistant-Gerät einem Asset zuordnen, eine zugehörige Entität demselben Asset zuweisen und
    den aktuellen Wert in der Asset-Detailansicht prüfen.
13. `Ctrl+K` drücken und prüfen, dass der Cursor sofort im Suchfeld steht.
14. Eine Wiki-Seite archivieren und über **Archiv → Wiki** schreibgeschützt öffnen.
15. Container neu starten und Persistenz bestätigen.

## Definition of Done

- [x] Datenmodell, Migration, Repository, Service und lokale API umgesetzt.
- [x] Responsive Geräte-, Netz-, Schnittstellen-, Adress-, Verbindungs- und Topologieoberfläche.
- [x] Asset-, Dashboard-, Such-, Dokument- und Qualitätsintegration.
- [x] Service-, API-, Migrations-, Such- und Frontend-Clienttests ergänzt.
- [x] Python-Syntax, Frontend-Skriptsyntax, relative Imports und Migrationskette statisch geprüft.
- [ ] Vollständiger Docker-Build und automatisierte Tests im Zielsystem.
- [ ] Praktische Betreiberabnahme.

## Nicht Bestandteil

Automatische Netzwerkerkennung, SNMP, LLDP/CDP, Portscan, Ping- oder Verfügbarkeitsüberwachung,
Konfigurationsbackup von Netzwerkgeräten, DNS-/DHCP-Synchronisierung, Zugangsdatenverwaltung,
NetBox-Import und automatische Home-Assistant-Zuordnung.
