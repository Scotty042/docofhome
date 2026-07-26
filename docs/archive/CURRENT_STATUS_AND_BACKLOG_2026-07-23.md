# DocOfHome – aktueller Projektstatus, Testbefunde und nächste Arbeitsschritte

> **Dokumentstand:** 23. Juli 2026  
> **Letzter bekannter Quellstand:** `0.1.18-dev` – Sprint 0033 Verbrauchsmodul, Testpaket  
> **Sichtbarer Produktname:** `DocOfHome`  
> **Aktueller Arbeitsmodus:** Befunde sammeln; keine Korrekturen umsetzen, bis der Betreiber ausdrücklich die Weiterentwicklung freigibt.

Dieses Dokument ist die verbindliche Übergabe für den nächsten Entwicklungsdurchlauf. Es bündelt den bekannten Implementierungsstand, ausdrückliche Betreiberfreigaben, noch offene Abnahmen, sämtliche seit dem letzten Testpaket gesammelten Befunde und die geplante Reihenfolge der weiteren Entwicklung.

## 1. Bekannter Sprint- und Freigabestatus

### Ausdrücklich freigegeben

- Sprint 0027 – Nextcloud-Dokumentenspeicher
- Sprint 0032 – Netzwerkmodul

### Implementiert, aber nicht ausdrücklich abschließend freigegeben

- Sprint 0028 – Dokumentverknüpfungen
- Sprint 0029 – Wiki und Notizen
- Sprint 0030 – Wartungen, Aufgaben und Erinnerungen
- Sprint 0031 – Dokumentationsqualität
- Sprint 0033 – Verbrauchsmodul

### Nächste formale Sprints

1. Sprint 0033 zunächst korrigieren, vollständig testen und vom Betreiber freigeben lassen.
2. Sprint 0034 – Import, Export und Änderungshistorie
3. Sprint 0035 – geführter, modulübergreifender Einrichtungsassistent
4. Sprint 0036 – Stabilisierung und Vorbereitung von Version 1.0

Der Einrichtungsassistent bleibt bewusst hinter den Fachmodulen. Sein Sprintvertrag darf erst erstellt werden, wenn Netzwerk, Verbrauch und Import/Export stabil sind, damit der Assistent die tatsächlich fertigen Module integrieren kann.

## 2. Verbindliche nächste Aktion

Bis zur ausdrücklichen Betreiberanweisung werden nur weitere Fehler, Beobachtungen und Wünsche gesammelt.

Sobald der Betreiber die Korrekturrunde freigibt, ist in dieser Reihenfolge vorzugehen:

1. alle Punkte aus Abschnitt 3 fachlich und technisch prüfen
2. Konflikte oder Abhängigkeiten zwischen den Punkten auflösen
3. Sprint-0033-Korrekturpaket erstellen
4. Migrationen, Backend-Import, Frontend-Build, MDI-Icons und Docker-Build vollständig prüfen
5. ein vollständiges neues ZIP bereitstellen
6. Betreiberabnahme durchführen
7. erst danach Sprint 0034 beginnen

## 3. Gesammelte Befunde und Anforderungen

### 3.1 Mobile Zählerstandserfassung

Die Erfassung von Zählerständen ist primär für das iPhone zu optimieren. Das Anlegen und die umfangreiche Verwaltung von Zählern darf weiterhin desktoporientiert bleiben.

Anforderungen:

- große, gut erreichbare Eingabeflächen
- Zählerstand als prominentestes Eingabefeld
- numerische iPhone-Tastatur über passende Feldtypen und `inputmode`
- Dezimaleingabe passend zur konfigurierten Genauigkeit
- Einheit direkt am Eingabefeld sichtbar
- Datum und Uhrzeit sinnvoll vorbelegt
- möglichst wenige Pflichtfelder
- Foto, Kommentar und Speichern schnell erreichbar
- keine gedrängte Desktop-Tabelle im mobilen Eingabefluss
- Orientierung an der Bedienung der früheren Verbrauchserfassungs-App

### 3.2 Responsive Verbrauchsstatistiken

Die aktuellen Diagramme sind zu statisch und bei vielen Monaten oder kleinen Displays zu klein.

Anforderungen:

- responsive Diagrammgröße
- größere Balken und Beschriftungen auf dem Smartphone
- horizontal scrollbare Zeitachse, wenn nicht alle Monate lesbar darstellbar sind
- weniger Monate gleichzeitig auf kleinen Displays
- Antippen eines Balkens zeigt Wert und Zeitraum als Tooltip
- Diagrammbereich aufklappbar oder vergrößerbar
- optionaler Vollbildmodus pro Diagramm
- keine überlappenden Monatsbeschriftungen
- physische und virtuelle Zähler gleichwertig lesbar
- sinnvoller Wechsel zwischen Monats- und Jahresansicht

### 3.3 Verbrauch auf dem Dashboard

Die Dashboard-Kachel „Integrationen“ wird nicht benötigt. Eine allgemeine Kachel „Verbrauch“ ist zu wenig aussagekräftig.

Stattdessen sollen direkte Vergleichswerte angezeigt werden für:

- Hauptwasser
- Strom
- Gas

Je Medium:

- Verbrauch des aktuellen Monats
- Verbrauch des vorherigen Monats
- absolute Differenz
- prozentuale Veränderung
- klare Kennzeichnung für gestiegen oder gefallen
- fehlende Vergleichswerte nicht als falsche Nullwerte behandeln
- die tatsächlich als Hauptzähler definierten Zähler verwenden
- mobil kompakt und gut lesbar

### 3.4 Dashboard konfigurierbar – nur Desktop

Die Dashboard-Bearbeitung wird ausschließlich auf Desktop angeboten.

Anforderungen:

- Bearbeiten-Schaltfläche nur in Desktopansichten
- Kacheln ein- und ausblenden
- Reihenfolge per Drag-and-drop ändern
- Standardlayout wiederherstellen
- ausgeblendete Kacheln wieder aktivieren
- gespeicherte Reihenfolge gilt auch für die mobile Darstellung
- auf dem iPhone keine Bearbeitungs- oder Verschiebefunktionen
- wichtige Warnungen bleiben mindestens über einen separaten Bereich erreichbar

### 3.5 Wartungen und Aufgaben frühzeitig anzeigen

Offene Wartungen und Aufgaben sollen bereits drei Tage vor Fälligkeit auf dem Dashboard erscheinen.

Statusdarstellung:

- in den nächsten drei Tagen fällig
- heute fällig
- überfällig

Zusätzlich:

- Datum und verbleibende Tage anzeigen
- erledigte und abgebrochene Einträge ausblenden
- bei wiederkehrenden Wartungen nur die nächste offene Fälligkeit berücksichtigen

### 3.6 Kalenderbasierte Wiederholungen

Neben „alle X Tage nach Erledigung“ werden kalenderbasierte Wiederholungen benötigt.

Unterstützte Varianten:

- monatlich an einem festen Kalendertag, beispielsweise am 1. oder 30.
- letzter Tag des Monats
- alle zwei, drei, sechs oder zwölf Monate
- jährlich an einem festen Datum
- fehlender Kalendertag, etwa 30. Februar, fällt auf den letzten verfügbaren Tag des Monats

Die beiden Bedeutungen müssen getrennt bleiben:

- **intervallbasiert:** X Tage nach der tatsächlichen Erledigung
- **kalenderbasiert:** fester Kalendertag unabhängig vom Erledigungsdatum

### 3.7 Zählerableseerinnerungen

Kalenderbasierte Wiederholungen sollen insbesondere für Zählerablesungen nutzbar sein.

Anforderungen pro Zähler:

- Ablesung jeden Monat an einem festen Tag
- alternativ am letzten Tag des Monats
- optional weitere Erinnerungstage, wenn noch keine Ablesung vorhanden ist
- Dashboardanzeige bereits drei Tage vorher
- direkte Aktion „Jetzt ablesen“
- Erinnerung verschwindet nach einer passenden Ablesung für den Zeitraum
- Monatszuordnung eindeutig halten
- freie, unregelmäßige Ablesungen weiterhin zulassen

### 3.8 Globale Inventarnummern

Inventarnummern müssen global über alle Assets eindeutig und fortlaufend sein.

Anforderungen:

- der Plus-Button schlägt die nächste freie Inventarnummer vor
- Nummerierung beginnt nicht je Asset-Typ, Raum oder Kategorie erneut bei 1
- bereits verwendete Nummern werden übersprungen
- archivierte Assets reservieren ihre Inventarnummer dauerhaft
- manuelle Eingabe bleibt möglich, aber Duplikate werden verhindert
- Eindeutigkeit im Backend beziehungsweise in der Datenbank absichern
- gleichzeitige Anlage darf keine doppelte Nummer erzeugen

### 3.9 Einheitlicher sichtbarer Produktname

Der sichtbare Name lautet überall exakt **DocOfHome**.

Projektweit prüfen:

- `Tectoryn`
- `tectoryn`
- sichtbares `JARVIS` oder `Jarvis`
- sichtbares `docofhome`, `Docofhome` oder andere Schreibweisen
- Seitentitel, Tooltips, Hilfetexte, Platzhalter, Dialoge und Beschreibungen

Interne technische Legacy-Bezeichner dürfen für Daten- und Updatekompatibilität bestehen bleiben, solange sie nicht für den Benutzer sichtbar sind.

### 3.10 Home Assistant: Gerät und Entitäten am Asset

Fachliches Zielmodell:

- ein physisches Home-Assistant-Gerät entspricht normalerweise einem DocOfHome-Asset
- die Entitäten des HA-Geräts werden als aktuelle Eigenschaften beziehungsweise Messwerte des Assets dargestellt
- Spannung, Leistung, Energie, Temperatur und andere Entitäten erzeugen nicht automatisch weitere Assets
- explizite Entitätszuordnungen müssen im Asset sichtbar sein
- aktueller Zustand, Einheit, Verfügbarkeit und letzter Aktualisierungszeitpunkt anzeigen
- beim Zuordnen einer Entität automatisch das Asset vorschlagen, dem das übergeordnete HA-Gerät bereits zugeordnet ist
- mehrere HA-Geräte dürfen bewusst demselben Asset zugeordnet werden, wenn sie zusammen eine Anlage bilden

Dieser Bereich wurde im Sprint-0032-Teststand teilweise erweitert, muss aber in der nächsten Korrekturrunde vollständig regressionsgeprüft werden.

### 3.11 Globale Suche

Zu prüfen beziehungsweise als Regressionstest festzuhalten:

- `Ctrl+K` öffnet die Suche
- Fokus und Cursor befinden sich sofort im Suchfeld
- erster Mausklick öffnet und fokussiert die Suche
- Nextcloud-Dokumente werden gefunden
- Wiki-, Netzwerk- und spätere Verbrauchsdaten erscheinen gemäß Suchvertrag

### 3.12 Wiki-Archiv

Archivierte Wiki-Seiten müssen im Archiv sichtbar und schreibgeschützt aufrufbar sein.

Zu prüfen:

- Archiv enthält eigene Wiki-Kategorie
- archivierte Seite lässt sich öffnen
- Suche und Direktnavigation behandeln archivierte Inhalte korrekt
- keine Bearbeitung ohne Wiederherstellung

### 3.13 Netzwerk: VLAN optional

VLAN wird im Heimnetz nicht zwingend verwendet.

Anforderungen:

- VLAN-ID überall optional
- leere VLAN-Felder sind gültig
- keine Pflichtvalidierung oder leere Zeichenfolge als fehlerhafter API-Wert
- Topologie und Adressverwaltung funktionieren vollständig ohne VLAN

### 3.14 Switch-Ports automatisch erzeugen

Bei Switches soll die Portanzahl angegeben werden können, statt beispielsweise 48 Ports einzeln anzulegen.

Anforderungen:

- Feld „Anzahl Ports“
- automatische Porterstellung
- wählbares Namensschema, etwa `1–48`, `Gi1/0/1–Gi1/0/48` oder `eth1–eth48`
- vorhandene Ports nicht duplizieren
- Erhöhung ergänzt nur fehlende Ports
- Reduzierung löscht belegte oder verbundene Ports niemals automatisch
- optional getrennte Anzahlen für Kupfer-, SFP/SFP+- und Uplink-Ports
- Standardgeschwindigkeit und PoE-Fähigkeit für erzeugte Ports
- einzelne Ports bleiben separat bearbeitbar

### 3.15 Switch-Portbelegung und dokumentierter Netzwerkpfad

DocOfHome soll zeigen, welches Gerät an welchem Port hängt und über welche Zwischenstationen ein Endgerät erreichbar ist.

Beispiele:

```text
FRITZ!Box LAN 1 → Switch Port 1 → Switch Port 3 → PC
FRITZ!Box LAN → Switch Port 1 → Switch Port 2 → Repeater LAN 1 → WLAN → Smartphone
```

Anforderungen:

- Portübersicht am Switch mit Status, Gegenstelle, Port und Geschwindigkeit
- grafische Frontansicht des Switches
- kabelgebundene, drahtlose, Mesh- und logische Verbindungen unterscheiden
- Funktion „Verbindungspfad anzeigen“ je Netzwerkgerät
- kein klassisches IP-Traceroute-Versprechen; dargestellt wird der dokumentierte physische und logische Pfad
- Schleifen und widersprüchliche Verbindungen erkennen

### 3.16 FRITZ!Box-Integration

Eine optionale, zunächst ausschließlich lesende FRITZ!Box-Integration ist sinnvoll.

Mögliche Daten:

- Gerätename
- IPv4- und IPv6-Adresse
- MAC-Adresse
- online oder offline
- LAN oder WLAN
- Frequenzband und Verbindungsrate
- Verbindung über FRITZ!Box oder Repeater
- zuletzt bekannte Verbindung
- feste DHCP-Zuordnung, soweit verfügbar

Leitplanken:

- offizieller beziehungsweise stabiler lokaler Zugriff bevorzugt, beispielsweise TR-064
- eigener FRITZ!Box-Benutzer mit minimalen Rechten
- MAC-Adresse als primäre Zuordnung zu Assets
- unbekannte Geräte nur als Vorschläge
- keine ungefragte Anlage oder Überschreibung
- manuelle Portdokumentation bleibt führend für fremde Switches

### 3.17 Docker-Container und logische Dienste

Docker-Container werden nicht als eigene physische Assets, sondern als logische Dienste oder Workloads unter einem Host-Asset dargestellt.

Datenmodell:

- Host-Asset
- Container- beziehungsweise Dienstname
- Image und Tag
- Compose-Projekt
- Netzwerkmodus: Bridge, Host, Macvlan oder eigenes Docker-Netz
- Container-Ports und veröffentlichte Host-Ports
- interne, externe, administrative und API-URLs
- Reverse-Proxy-Zuordnung
- Dienstabhängigkeiten
- Status
- Dokumente, Notizen und Wartungen

Topologie:

- Container innerhalb ihres Hosts gruppieren
- Portmapping sichtbar machen
- Reverse-Proxy-Pfad darstellen
- Macvlan-Container dürfen zusätzlich eine eigene IP besitzen, bleiben aber dem Host zugeordnet

### 3.18 Nextcloud- und UI-Regressionen

Frühere Korrekturen bleiben als Regressionstests bestehen:

- leere Nextcloud-Ordner lassen sich löschen
- nicht leere Ordner bleiben geschützt
- Ordnerbaum zur Auswahl des Verschiebeziels
- Nextcloud-Dateien in globaler Suche
- Icons in schmalen Schutzgeräten werden nicht abgeschnitten
- Augen-Icon für Versorgungsbaum
- vollständige MDI-Icon-Prüfung vor Paketübergabe

## 4. Sprint 0033 – bestehende Verbrauchsdaten

Der Quellcode der früheren Verbrauchserfassung wurde als
`verbrauchserfassung-ugreen-nas-v1.4.3(1).zip` bereitgestellt und dient als fachliche Referenz.

Die hochgeladene Datei `verbrauch(1).sqlite` ist technisch intakt, enthält aber nur Anwendungseinstellungen und keine Tabellen `meters`, `readings` oder `notes`. Wahrscheinliche Ursachen:

- die aktive Datenbank lag an einem anderen Pfad
- bei einer laufenden SQLite-WAL-Datenbank wurden `-wal` und `-shm` nicht mitkopiert
- es wurde eine nicht aktive oder bereits geleerte Datenbankdatei kopiert

Für die tatsächliche Migration vorhandener Zähler und Ablesungen wird noch eine konsistente Datenbankkopie benötigt. Bevorzugt:

```bash
sqlite3 /pfad/verbrauch.sqlite ".backup '/pfad/verbrauch-backup.sqlite'"
```

Alternativ Container kurz stoppen und anschließend die Datenbankdatei sowie vorhandene
`verbrauch.sqlite-wal` und `verbrauch.sqlite-shm` gemeinsam sichern.

Alte Zugangsdaten, Tokens und Secrets werden nicht importiert.

## 5. Sprint 0034 – vorgesehener Umfang

Sprint 0034 beginnt erst nach Abschluss und Freigabe von Sprint 0033.

Vorgesehener Umfang:

- vollständiger JSON-Export der DocOfHome-Fachdaten
- CSV-Export einzelner Module
- Importvorschau
- Spaltenzuordnung
- Dubletten- und Konflikterkennung
- kontrollierte Übernahme älterer DocOfHome-Datenstände
- nachvollziehbare Änderungshistorie mit Objekt, Zeitpunkt und Änderung
- keine Passwörter, Tokens oder Secrets in normalen Exporten

## 6. Sprint 0035 – geführter Einrichtungsassistent

Der Assistent wird erst nach den Fachmodulen umgesetzt.

Geplanter Ablauf:

1. auswählen, was angelegt werden soll
2. bestehendes Objekt oder Home-Assistant-Gerät auswählen
3. Asset, Typ, Produkt und Ort erfassen
4. elektrische Zuleitung und nachgelagerte Komponenten auswählen
5. Phase, Leiter, Kabel und Eigenschaften erfassen
6. Schutzgerät, Position und Stromkreis anlegen oder zuordnen
7. Netzwerk- und Verbrauchsdaten integrieren, sofern relevant
8. Bilder aus Immich und Dokumente aus Nextcloud verknüpfen
9. noch nicht vorhandene Komponenten als offene Notiz oder Entwurf vormerken
10. vollständige Vorschau
11. möglichst transaktionales Speichern und Zurückrollen

Der Assistent darf keine technischen Angaben erraten, muss Duplikate vermeiden und Entwürfe fortsetzen können.

## 7. Qualitätsgates für das nächste Paket

Vor Übergabe des nächsten ZIP mindestens prüfen:

- vollständiger FastAPI-Import
- Alembic-Upgrade und -Downgrade
- Fresh-Database-Test
- Ruff
- mypy
- vollständige Pytest-Suite
- Vitest
- `vue-tsc --noEmit`
- Vite-Produktionsbuild
- MDI-Icon-Checker
- Docker-Build mit Backend-Smoke-Test
- zentrale mobile Abläufe auf iPhone-Breite
- Datenverlust- und Duplikatprüfungen
- sichtbare Produktbezeichnung ausschließlich `DocOfHome`

## 8. Startanweisung für die nächste Entwicklung

Nach ausdrücklicher Betreiberfreigabe:

> Verwende den neuesten vollständigen DocOfHome-Quellstand als verbindliche Basis. Lies zuerst
> `PROJECT_STATUS.md`, `ROADMAP.md`, den Vertrag zu Sprint 0033 und dieses Backlog. Setze alle
> gesammelten Punkte der Sprint-0033-Korrekturrunde um, prüfe die Qualitätsgates und liefere ein
> vollständiges neues ZIP. Beginne Sprint 0034 erst nach Betreiberabnahme von Sprint 0033.
