# Changelog

## 1.6.1 – 2026-07-27

### Geändert

- Zählerwechsel ist ein eigener atomarer Vorgang; normale Ablesungen enthalten
  keine Reset-Option mehr und zeigen den letzten Stand sowie passende
  OBIS-Hinweise.
- Mehrere ausgewählte PV-Zähler werden im Dashboard gemeinsam ausgewertet.
- Online-Produktbildquellen sind einzeln konfigurierbar; Ergebnisse aktivierter
  Quellen werden kombiniert, dedupliziert und nach Relevanz sortiert.
- Asset-Details zeigen direkte elektrische Einspeisungen und Weiterführungen;
  Phasenabgänge werden nach L1, L2, L3, mehrphasig und nicht zugeordnet gruppiert.
- Sicherungs-/Schutzgeräte werden zentral klassifiziert und einheitlich gezählt.
- Netzwerkschnittstellen können als primär markiert werden.

### Hinzugefügt

- ausführliche Hilfetexte zur Energiebilanz;
- Home-Assistant-Rollen für Schaltausgang, Eingang, Verfügbarkeit und Diagnose;
- Standard-Asset-Typ **Smartes Relais / DIN-Schaltaktor** und Produkt
  **Shelly Pro 1**;
- Migration `0038_release_1_6_1_corrections`.

## 1.6.0 – 2026-07-27

### Geändert

- Einrichtungsassistent setzt Integrationsmeldungen beim Schrittwechsel zurück
  und bietet nach dem Speichern eine zuverlässige Weiterleitung samt Fallback.
- Backup-Dateien verwenden den Namen DocOfHome; alte `tectoryn`-Dateinamen bleiben
  für Wiederherstellungen kompatibel.
- Online-Produktbildsuche verwendet DuckDuckGo Images mit Relevanzsortierung und
  Wikimedia Commons als Fallback.
- Sicherungs-/Zählerschrank ist für PC und Tablet kompakter, farbcodiert und
  zeigt primär Namen sowie optionale Live- oder B16-Kurzwerte.
- Wasser- und Gaszähler werden aus der elektrischen Platzierung herausgefiltert.

### Hinzugefügt

- Auslösecharakteristik und Nennstrom als Asset-Typ-Standard und Asset-Override.
- empfohlener Asset-Typ Stromstoßschalter mit Spulenspannung, Spannungsart,
  Kontaktanzahl und Kontaktart.
- Smart-Meter-Messpunkte für CT-Klemmen an vorhandenen Verkabelungen mit eigener
  Home-Assistant-Entitätszuordnung.
- Migration `0037_release_1_6_electrical_measurements`.
- ausführlichere Handbuchtexte zu Sammel-/Kammschiene und Stromwandlerklemmen.

## 1.5.0 – 2026-07-26

### Hinzugefügt

- statische Offline-Seite **Wiki → Handbuch & Glossar** mit 109 Begriffen aus
  allen zentralen DocOfHome-Bereichen;
- lokale Suche über Begriffe, Aliase, Beschreibungen, Beispiele und Kategorien;
- Kategorienfilter, einklappbare Abschnitte, Inhaltsverzeichnis, interne
  Ankerlinks und alphabetisches Glossar mit A–Z-Sprungmarken;
- responsive Desktop- und Mobilstruktur ohne externe Abhängigkeit;
- Elektro-Sicherheitshinweis und verständliche Privathaushaltsbeispiele;
- Button **Asset bearbeiten** in der Detailansicht von Schutzgeräten und
  normalen DIN-Assets.

### Geändert

- Navigation gruppiert die bestehenden editierbaren Wiki-Seiten und das neue
  Handbuch sichtbar unter **Wiki**;
- passive Schrankkomponenten bleiben bewusst ohne Asset-Bearbeitung.

### Datenmodell

- keine neue Migration; Alembic-Head bleibt `0036`;
- Handbuchinhalte liegen ausschließlich in einer zentralen Frontend-Datenstruktur.


Alle wesentlichen Änderungen an DocOfHome werden hier dokumentiert.

## 1.4.2 – 2026-07-25

### Geändert

- Impressum vollständig aus Info-Seite, Einstellungen und Settings-API entfernt;
- GitHub-/Projektverweise werden zentral im Quellcode statt pro Installation gepflegt;
- Feedbackformular direkt aktiviert und von der privaten Nextcloud-Integration entkoppelt;
- Feedback wird als begrenztes ZIP an einen fest hinterlegten öffentlichen Nextcloud File Drop übertragen.

### Sicherheit und Datenschutz

- ZIP enthält nur Feedbacktext, strukturierte Basisdaten und ausdrücklich freigegebene technische Angaben;
- Datenbank, Zugangsdaten, Tokens und Integrationskonfiguration werden nicht übertragen;
- serverseitige Größenbegrenzung und bestehendes Rate-Limit bleiben aktiv.

### Datenmodell

- Migration `0036_remove_configurable_about_fields` entfernt die nicht mehr benötigten konfigurierbaren About-, Impressums- und Feedbackfelder.

### Korrigiert

- Lockdatei verweist wieder auf die veröffentlichte transitive Abhängigkeit `rfdc@1.4.1`;
- Integrationsmetadaten und Pflichtfeldregel der Einstellungsseite wiederhergestellt, damit `vue-tsc` die bestehenden Integrationskarten korrekt auflösen kann.


## 1.4.1 – 2026-07-25

### Hinzugefügt

- neue Seite **Mehr → Über DocOfHome** mit Projektbeschreibung, zentraler
  Versionsanzeige, Release Notes, optionalen Projektlinks und Impressum;
- sichere, strukturierte Darstellung der ausgelieferten Markdown-Release-Notes
  ohne ausführbares HTML;
- optionales Feedbackformular mit sichtbarer Zustimmung für technische
  Metadaten und serverseitigem Upload in einen festen Nextcloud-Ordner;
- konfigurierbare Projekt-, Lizenz-, Impressums- und Feedbackangaben in den
  Einstellungen;
- direkter Dashboard-Button **Zählerstände erfassen** für den mobilen Alltag.

### Geändert

- Versionskachel vom Dashboard entfernt;
- alte gespeicherte Dashboard-Layouts werden automatisch auf die verbleibenden
  Kacheln normalisiert;
- Release Notes und Changelog werden in das Laufzeitimage übernommen.

### Datenmodell

- Migration `0035_about_page_and_feedback` ergänzt optionale Felder in
  `application_settings`; bestehende Fachdaten bleiben erhalten.


## 1.4.0 – 2026-07-24

### Hinzugefügt

- dreiphasige Sammelschienen mit TE-Bereich, wählbarer Startphase und automatisch
  wiederholter Phasenfolge;
- einfache FI-Gruppen: Sammelschienen und N-Schienen können einem FI/RCD
  zugeordnet werden;
- Schutzgeräte übernehmen FI, N-Schiene und Phase automatisch aus ihrer
  Position unter einer Sammelschiene, können aber bei Bedarf manuell abweichend
  dokumentiert werden;
- verständliche Warnungen bei abweichender FI-Zuordnung, falscher N-Schiene,
  fehlender N-Schiene und über das Schienenende hinausragenden Geräten;
- optimierte Schrankansicht mit Belegungsübersicht, Kompakt-/Erweitert-Modus,
  sichtbarer Sammelschiene, Phasenkennzeichnung, Detailleiste und eigenem Bereich
  für nicht platzierte DIN-Geräte.

### Datenmodell

- Migration `0034_home_electrical_groups` ergänzt FI-Verknüpfungen,
  Neutralleiterschienen-Zuordnungen und die Startphase von Sammelschienen;
- bestehende Schutzgeräte, Schrankkomponenten, Verkabelungen und Platzierungen
  bleiben erhalten; alle neuen Felder sind optional.


## 1.3.2 – 2026-07-24

### Korrigiert

- bestehende Installationen entfernen mit Migration `0033` zuverlässig den
  historischen Unique-Index, der trotz bereits angewendeter Migration `0027`
  weiterhin nur eine Einspeisung je Ziel zulassen konnte;
- Phasenverteilerblöcke und andere Schrankkomponenten können nach dem Update
  tatsächlich mehrere Quellen gleichzeitig erhalten;
- Datenbankkonflikte der elektrischen Topologie werden verständlich auf Deutsch
  ausgegeben und weisen bei einer veralteten Datenbank gezielt auf Migration
  `0033` hin.

### Datenmodell

- Migration `0033_remove_legacy_single_target_topology_index` entfernt nur den
  alten Ziel-Unique-Index. Verbindungen und sonstige Bestandsdaten bleiben
  unverändert.

## 1.3.1 – 2026-07-24

- Build-Fix: Das Home-Assistant-Assetformular initialisiert `module_width` vollständig und erfüllt wieder `AssetWrite`.

### Korrigiert

- normale DIN-Assets wie Smart Meter werden mit ihrer vollständigen TE-Breite
  direkt im Schienenraster dargestellt;
- Drag-and-drop verschiebt Schutzgeräte und DIN-Assets in einfacher und
  strukturierter Reihenaufteilung;
- laufende Verbrauchsmonate enden bei „heute“ und verlangen keine Ablesung aus
  der Zukunft oder sekundengenaue Endablesung.

### Erweitert

- optionale DIN-Breite direkt an Asset-Typen und Assets; Produkte bleiben
  optional, die wirksame Reihenfolge lautet Asset vor DIN-Produkt vor Asset-Typ;
- Schrankkomponenten unterstützen mehrere eingehende Einspeisungen;
- Leiter werden an Schrankkomponenten gegen konfigurierte und tatsächlich
  eingespeiste L1/L2/L3/N/PE geprüft; ein L1-zu-L2-Umetikettieren ist nicht
  möglich;
- Topologie und Inline-Verkabelungsanzeige zeigen alle eingehenden Verbindungen.

### Datenmodell

- Migration `0032_asset_and_type_din_width` ergänzt validierte nullable
  DIN-Breiten an Asset-Typen und Assets.

## 1.3.0 – 2026-07-24

### Hinzugefügt

- passive Schrankkomponenten als eigene, nicht als Asset geführte Objekte:
  Phasenverteilerblock, Sammel-/Phasenschiene, N-/PE-Schiene, Reihen- und
  Anschlussklemme, Potentialverteiler und sonstige Komponente;
- Platzierung auf DIN-Schienen mit Reihe, TE-Startposition, TE-Breite,
  Leiterzuordnung und optionalen technischen Daten;
- neuer Elektro-Endpunkttyp `cabinet_component` für Verkabelung und
  Versorgungstopologie;
- Darstellung und Bearbeitung der Komponenten in einfacher Reihenaufteilung und
  strukturiertem Feld-/Bereichsmodus.

### Korrigiert

- Drag-and-drop von Schutzgeräten funktioniert auch bei Unterverteilungen mit
  einfacher Reihenaufteilung;
- Serienanlage fordert im Reihenmodus keinen DIN-Bereich mehr an;
- DIN-Assets können im Reihenmodus ohne `area_id` platziert werden;
- Überschneidungen zwischen Schutzgeräten, DIN-Assets und Schrankkomponenten
  werden gemeinsam geprüft;
- verkabelte Schrankkomponenten können nicht versehentlich archiviert werden.

### Datenmodell

- Migration `0031_cabinet_components_and_rows_placements` ergänzt die neue
  Schrankkomponententabelle, nullable Bereichs-IDs für Reihen-Platzierungen und
  den neuen Verkabelungsendpunkt.

## 1.2.4 – 2026-07-24

### Korrigiert

- Online-Produktbildsuche um einen Browser-Fallback über die offizielle
  Wikimedia-API mit `origin=*` ergänzt. Backend-Suche bleibt bevorzugt; der
  gewählte Treffer wird lokal gespeichert.
- Fehlerzustände für Backend-Ausfall, externe Nichterreichbarkeit, leere
  Trefferlisten und fehlgeschlagene Bilddownloads getrennt dargestellt.
- HTTP-500-Fehler der Netzwerkübersicht durch die fehlende Einbindung von
  `NetworkInterfaceType` behoben; alte oder unbekannte Enum-Werte werden robust
  auf neutrale Standardwerte abgebildet.
- Netzwerkseite lädt Teilendpunkte fehlertolerant und behält erfolgreich
  geladene Daten bei.
- Schrankaufteilung ist für Haupt- und Unterverteilungen aufrufbar; einfache
  Reihen werden auf der Layoutseite dargestellt und leere Verteilungen erhalten
  eine klare Anlageaktion.
- Unterverteilungen unterstützen den Feld-/Bereichsmodus einschließlich
  Zählerbereichen, N-/PE-Schienen und DIN-Geräten.
- globale Benachrichtigungswarteschlange oberhalb von Dialogen eingeführt;
  mobile Zählerstandserfassung bleibt bei Fehler geöffnet und verhindert
  Mehrfachspeichern.
- Frontend-Regressionsprüfungen lesen Vue-Quelldateien über Vite-`?raw`-Imports
  statt über `node:fs`. Dadurch benötigt `vue-tsc --noEmit` keine separat
  eingebundenen Node-Typdeklarationen mehr.

### Datenmodell und Kompatibilität

- Migration `0030_enable_subdistribution_sections` entfernt ausschließlich die
  frühere Reihenmodus-Pflicht für Unterverteilungen;
- bestehende Daten bleiben erhalten;
- Docker-/Compose-Architektur und Einzelcontainer bleiben unverändert.

## 1.2.3 – 2026-07-24

### Korrigiert

- Frontend-TypeScript-Buildfehler in `immichGallery.test.ts` behoben: Das
  Test-Fixture enthält nun das Pflichtfeld
  `online_product_image_search_enabled`.
- `selectedImmichAlbumId` akzeptiert nur noch
  `Pick<ConfigurationRead, 'integrations'>`, da die Funktion keine anderen
  Konfigurationswerte benötigt. Dadurch bleiben Tests bei späteren unabhängigen
  Konfigurationserweiterungen stabil.

### Kompatibilität

- keine Änderung an API oder Datenmodell;
- keine neue Alembic-Migration; Head bleibt `0029`;
- direkter Patch von 1.2.2 ohne Datenmigration.

## 1.2.2 – 2026-07-24

### Korrigiert

- Frontend-Buildfehler in der MDI-Prüfung behoben: Das in `@mdi/font` 7.4.47
  nicht vorhandene `mdi-label-plus-outline` wurde im Asset-Labeldialog an beiden
  Stellen durch `mdi-tag-plus-outline` ersetzt.
- Versions- und Releasedokumentation auf 1.2.2 aktualisiert.

### Kompatibilität

- keine Änderung an API oder Datenmodell;
- keine neue Alembic-Migration; Head bleibt `0029`;
- direkter Patch von 1.2.1 ohne Datenmigration.

## 1.2.1 – 2026-07-24

### Dokumentation und Planung

- aktuellen Projektstatus, offenen Backlog und Qualitätsgates eindeutig
  dokumentiert;
- zentrales Sprintregister eingeführt;
- historischen Projektplan `0.1.18-dev` vollständig archiviert und aus dem
  aktiven Planungsweg entfernt;
- ältere Sprintverträge als historische Verträge gekennzeichnet, ohne ihre
  damaligen Statusangaben rückwirkend zu verändern;
- Sprint 0039 „Über DocOfHome, Changelog, Impressum und Feedback“ als nicht
  freigegebenen Entwurf aufgenommen;
- README, Roadmap, Projektstatus, Audit und Implementierungsfortschritt auf den
  aktuellen Stand vereinheitlicht.

### Kompatibilität

- keine Änderung an Anwendungscode, API oder Datenmodell;
- keine neue Alembic-Migration; Head bleibt `0029`;
- Funktionsumfang und Datenkompatibilität entsprechen 1.2.0.

## 1.2.0 – 2026-07-23

### Hinzugefügt

- mehrere Home-Assistant-Geräte und -Entitäten je Asset mit fachlichen Rollen
  einschließlich primärer Live-Anzeige, Leistung, Spannung, Strom, Energie und
  phasenbezogenen Werten;
- allgemeine DIN-Hutschienengeräte auf Basis von Produktbauform und TE-Breite
  sowie kompakte HA-Livewerte direkt in der Zählerschrankansicht;
- Produktbild-Upload, visuelle Immich-Auswahl, kontrollierbare Wikimedia-Suche
  mit lokaler Speicherung und weiterhin manuelle Bild-URL;
- Asset-Duplizierung und Serienanlage mit Namensschema, optionaler
  fortlaufender TE-Platzierung und sicherem Ausschluss eindeutiger Gerätedaten;
- Inline-Anlage von Labels im Asset-Formular;
- einklappbare Navigationsgruppe **Mehr** für selten verwendete Bereiche.

### Leistung und Bedienung

- HA-Geräte werden mit 50 und Entitäten mit 100 Einträgen je Seite
  serverseitig übertragen; Suche, Bereich, Domain, Gerät, Geräteklasse, Einheit
  und Verfügbarkeit werden vor der Antwort gefiltert;
- Entitäten werden erst beim Öffnen des Bereichs, bei einer Suche oder nach
  Geräteauswahl geladen; Mehrfachauswahlen bleiben über Seiten erhalten;
- parallele HA-Aktualisierungen werden zu genau einem Lauf zusammengeführt;
  Registerdaten werden 15 Minuten und Livezustände 30 Sekunden gecacht;
- große JSON-Antworten können per Gzip übertragen werden;
- Asset- und DIN-Platzierungslisten vermeiden zusätzliche Einzelabfragen,
  aktive Schutzgeräte werden direkt statt über Vollscans gefiltert.

### Elektro und Datenmodell

- halbe Schrankbereiche besitzen eine eindeutige Seite **links** oder **rechts**;
  zwei Hälften dürfen dieselbe Ebene belegen, volle Bereiche nicht überdecken;
- Migration `0029_home_assistant_and_workflow_extensions` erhält bestehende
  1.1.3-Daten und führt neue Felder, Rollen und DIN-Platzierungen additiv ein;
- das nicht verfügbare Icon `mdi-ground-wire` bleibt ausgeschlossen; PE nutzt
  weiterhin `mdi-earth`.

### Sicherheit

- Produktbilder werden nach MIME-Typ, Größe und Dateisignatur geprüft;
- Online-Importe sind standardmäßig deaktiviert, auf Wikimedia-Hosts begrenzt,
  folgen keinen Redirects und werden lokal gespeichert.

## 1.1.3 – 2026-07-23

### Korrigiert

- Docker-/Frontend-Build brach bei der MDI-Prüfung ab, weil `mdi-ground-wire`
  in `@mdi/font` 7.4.47 nicht vorhanden ist.
- Die PE-Schiene verwendet nun das verfügbare und fachlich passende Icon
  `mdi-earth`.
- Der GitHub-CI-Workflow nutzt im Frontend `npm ci`, damit exakt die
  festgeschriebenen Lockfile-Versionen installiert werden.

### Kompatibilität

- Keine Datenbankmigration; Alembic-Head bleibt
  `0028_collected_integration_fixes`.
- Der vollständige Funktionsumfang und alle Daten aus 1.1.2 bleiben erhalten.


## 1.1.2 – 2026-07-23

### Hinzugefügt

- Asset- und Ortszuordnung direkt im Zählereditor; der Asset-Ort dient als
  rückwärtskompatibler Fallback.
- Home-Assistant-Livewerte für aktuelle Gesamtleistung und Spannung je Zähler;
  initiale Abfragen verwenden den lokalen HA-Snapshot, eine manuelle
  Aktualisierung erzwingt einen frischen Abruf.
- Platzierung von Verbrauchszählern und eigenständigen Assets vom Typ
  **Zähler** in Zählerfeldern.
- eigene N- und PE-Schienen sowie halbe Schrankbereiche zur Darstellung auf
  derselben Ebene.
- Netzanschluss als echter externer Quellpunkt der Elektro-Topologie.
- logische Netzwerkschnittstellen/Bridges mit zugeordneten physischen Ports und
  Geräte-IP; Bridges mit Mitgliedsports können nicht versehentlich in einen
  physischen Porttyp umgewandelt werden.

### Geändert

- Immich-Bilder an Assets öffnen sich per Klick oder Tastatur in einer großen
  Vorschau.
- Ortsauswahlen werden hierarchisch nach Gebäude, Etage und Raum sortiert.
- Bei elektrischen Verteilungen sind nur Assets vom Typ
  **Elektrische Verteilung** auswählbar und serverseitig zulässig.
- Die FRITZ!Box-Übernahme legt IP-Adressen auf einer logischen LAN-/Management-
  Schnittstelle ab.
- Freie Switch-Ports werden neutral dargestellt; Warnungen bewerten die
  Netzwerkanbindung des gesamten Geräts statt jeden einzelnen Port.

### Datenbank und Qualität

- Migration `0028_collected_integration_fixes` mit geprüftem Upgrade-,
  Downgrade- und erneutem Upgradepfad.
- Regressionstests für alle zehn gesammelten Korrekturen ergänzt.


## 1.1.1 – 2026-07-23

### Korrigiert

- Ableseerinnerungen unter **Wartung & Aufgaben** berücksichtigen nun auch
  bestehende Zähler ohne monatlichen Ableseplan. Für diese Zähler greift
  rückwärtskompatibel die globale Fälligkeit nach der letzten Ablesung.
- Zähler ohne bisherige Ablesung erscheinen sofort als fällig.
- Der Abschnitt **Ableseerinnerungen** bleibt sichtbar und zeigt bei leerer
  Liste einen verständlichen Status statt vollständig zu verschwinden.

### Qualität

- Regressionstests für Intervall-Fälligkeit, Zähler ohne Ablesung und
  Erinnerungshorizont ergänzt.
- Keine Datenbankmigration; Alembic-Head bleibt `0027_energy_balance`.

## 1.1.0 – 2026-07-23

### Hinzugefügt

- Sprint 0038 „Photovoltaik und Energiebilanz“ mit Anschlussstammdaten,
  Bilanzzähler-Zuordnung und monatlichen Kennzahlen
- neuer Zählertyp `electricity_feed_in` für Netzeinspeisung
- beliebig viele PV-Quellen, Wechselrichter und Speicher mit optionaler
  Asset-Verknüpfung
- mehrere Energiequellen je Ziel in der Elektro-Topologie
- visuelle Immich-Auswahl direkt bei Zählerablesungen
- Ableseerinnerungen unter „Wartung & Aufgaben“
- Migration `0027_energy_balance` und zugehörige Regressionstests

### Geändert

- Statistikdiagramme skalieren jede Zähler-/Statistikserie mit ihrem eigenen
  Wertebereich
- Dashboard-Primärzähler für Strom und Gas werden zuverlässig übertragen; ohne
  explizite Markierung greift eine deterministische Fallback-Auswahl
- Elektro-Topologie ist ein gerichteter azyklischer Mehrquellen-Graph statt
  eines strikt einwurzeligen Baums
- Versionen, Release-Dokumentation, Manifest und Prüfsumme auf `1.1.0`
  aktualisiert

### Kompatibilität

- alle Korrekturen aus `1.0.0-fix2` bleiben enthalten
- bestehende Messwerte verbleiben unverändert im Verbrauchsmodul
- direkter Upgradepfad von Alembic `0026` auf `0027`

## 1.0.0 – 2026-07-23

### Hinzugefügt

- persistentes, auf Desktop konfigurierbares Dashboard mit separatem
  Warnbereich
- Primärzähler und Monatsvergleiche für Hauptwasser, Strom und Gas
- mobile Zählererfassung, Monats-/Jahresdiagramme, Vollbild und barrierearme
  Detailansicht
- kalenderbasierte Wartungen und monatliche Ableseerinnerungen
- globale, auch für archivierte Assets reservierte Inventarnummern
- Switch-Portgenerator, Frontansicht und deterministischer dokumentierter Pfad
- optionale read-only FRITZ!Box-Integration
- logische Dienste/Container unter Host-Assets
- vollständiger JSON-Export, modulbezogener CSV-Export/-Import,
  Importvorschau und Konfliktstrategien
- unveränderliche, redigierte Änderungshistorie
- elfteiliger geführter Fachassistent mit Entwürfen und transaktionalem Apply
- Migrationen 0024, 0025 und 0026

### Geändert

- sichtbarer Produktname vollständig auf `DocOfHome` vereinheitlicht
- Drei-Tage-Fälligkeiten und Ableseerinnerungen im Dashboard
- bestehende Home-Assistant-, Suche-, Wiki-, VLAN-, Nextcloud- und
  Archivabläufe durch Regressionstests abgesichert
- zentrale Versionsquelle und reproduzierbare Frontend-Lockdatei
- SQLite-Batchmigration 0024 wiederanlauffähig gemacht: Nach einem
  abgebrochenen Containerstart werden ausschließlich verwaiste
  `_alembic_tmp_*`-Arbeitstabellen bereinigt oder fertiggestellt, während die
  kanonischen Nutzdaten erhalten bleiben

### Sicherheit

- Integrations-URLs, Konten und Secrets fehlen in Export und Audit
- FRITZ!Box-Ziele auf lokale Adressen begrenzt; Redirects, unsicheres XML und
  übergroße Antworten werden abgewiesen
- kein Docker-Socket und keine privilegierten Containerrechte erforderlich

## 0.1.18-dev – Ausgangsbasis

Letzter Entwicklungsstand vor der Stabilisierung zu 1.0.0. Details der
Übergabe sind in `docs/archive/CURRENT_STATUS_AND_BACKLOG_2026-07-23.md` archiviert.

## 1.0.0 – Fixstand 2026-07-23

- Erst-Setup um FRITZ!Box sowie direkte Verbindungstests für Home Assistant, Immich, Nextcloud und FRITZ!Box erweitert.
- Geführte Erfassung von Etagen, Räumen und optionalen Außenbereichen im Erst-Setup ergänzt.
- Hinweise zu den benötigten lesenden Immich-API-Rechten direkt im Setup ergänzt.
- FRITZ!Box-TR-064-Verbindung auf die Standardports 49000/49443 korrigiert und Fehlermeldungen verbessert.
- Smart-Home-Ansicht lädt Geräte und Entitäten wieder unabhängig von einer zuvor leeren Sichtbarkeitsauswahl.
- Geführter Komponenten-Assistent bietet eine visuelle Immich-Bildauswahl aus dem konfigurierten Album.
- Nach erfolgreichem Abschluss des geführten Assistenten erfolgt eine Bestätigung und automatische Rückkehr zum Anfang.
- Neues DocOfHome-Favicon für den Browser-Tab ergänzt.

## 1.0.0 – Fixstand 2 vom 23.07.2026

### Korrigiert

- Globale Suche setzt den Fokus bei jedem Öffnen erneut; zusätzlich zu `Strg+K`/`Cmd+K` steht `/` als browserunabhängiges Tastenkürzel bereit.
- Dashboard-Kacheln lassen sich im Bearbeitungsmodus direkt ziehen, Drop-Ziele werden hervorgehoben und Änderungen erst nach „Speichern“ dauerhaft übernommen.
- Die geführte Einrichtung verwendet eine durchsuchbare Asset-Auswahl statt einer manuellen internen ID.
- Die Änderungshistorie zeigt verständliche Objekt- und Feldnamen, Vorher-/Nachher-Werte, Filter und direkte Objektverknüpfungen; RAW-Daten bleiben einklappbar.

### Hinzugefügt

- Dauerhaft erreichbarer Gebäudestruktur-Assistent unter `Bereiche & Räume > Geführt einrichten`, der vorhandene Etagen, Räume und Außenbereiche lädt und neue Einträge ohne stille Löschungen ergänzt.
- Eigener FRITZ!Box-Bereich im Netzwerkmodul mit Live-Geräteliste, Online-Status, IP/MAC, Verbindung, automatischer MAC-Zuordnung und bestätigter Übernahme in vorhandene Netzwerkgeräte.
- Vorbelegung des Asset-Editors aus einem unbekannten FRITZ!Box-Gerätevorschlag.

Die Produktversion bleibt bewusst `1.0.0`; es sind keine Datenbankmigrationen erforderlich.
