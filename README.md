# DocOfHome

DocOfHome 1.7.13.1 ist ein lokaler digitaler Zwilling für die technische
Hausdokumentation. Die Anwendung verwaltet Assets, Orte, Elektroinstallation,
Netzwerk, Verbrauch, Wartungen, Wiki, Bilder, Dokumente und optionale
Integrationen wie Home Assistant, Immich und Nextcloud.



## Neu in 1.7.13.1

- neu gestaltete, iPad-taugliche Rezeptansicht mit getrenntem Lesemodus und Editor
- ablenkungsfreier Vollbild-Kochmodus mit Touch-Checkboxen, Portionsskalierung und optionalem Screen Wake Lock
- eleganter Zutateneditor mit Autocomplete, Sortieren und Touch-Aktionen

## Neu in 1.7.12

- explizites, typisiertes MCP-Eingabeschema für das Speichern von Rezepten

## Neu in 1.7.11

- robuste MCP-Rezeptsuchantwort für leere Bestände und optionale Null-Filter

## Neu in 1.7.10

- korrigierter Frontend-Build des MCP-Handbucheintrags aus 1.7.9
- keine fachlichen oder Datenbankänderungen gegenüber 1.7.9

## Neu in 1.7.9

- erweiterte MCP-Abdeckung für Kochbuch, Wiki, Notizen, Assets, Orte und Stammdaten
- MCP-Zugriff auf Verbrauchszähler/Ablesungen sowie die Netzwerkdokumentation
- Löschen und Archivieren über MCP weiterhin ausschließlich mit Vollzugriff

## Neu in 1.7.8

- MCP per Bearer unter `/mcp` oder per Token-URL unter `/mcp/<token>`
- robuste zentrale Kopierfunktion, lesbarere Codefenster und Inline-Code
- sticky Speicherleiste und Verlassen-Warnungen bei ungespeicherten Einstellungen

## Neu in 1.7.7

- eigenständiges, strukturiertes Kochbuch unter Wiki mit Zutaten, Schritten, Suche,
  Kategorien, Tags, Bildern/Anhängen, Favoriten, Duplizieren, Portionsumrechnung und Druckansicht
- getrennte Modulschalter **Aktiviert** und **Im Hauptmenü anzeigen**; aktive ausgeblendete
  Module erscheinen dynamisch unter **Sonstiges**
- installierbare PWA mit Manifest, Standalone-Darstellung und updatefreundlichem Service Worker
- MCP-Anleitung vollständig im Handbuch/Runbook einschließlich funktionierender SWAG-Konfiguration
- Smart Home und Verbrauch werden als verfügbare Funktionen dargestellt
- Migration `0052` ergänzt Rezepte und Hauptmenü-Sichtbarkeit; Deaktivieren löscht keine Daten

## Neu in 1.7.6

- integrierter MCP-Server im bestehenden DocOfHome-Backend unter `/mcp`
- Konfiguration vollständig in **Einstellungen → Integrationen → ChatGPT / MCP**
- sicherer Bearer-Token, der nur einmal angezeigt und ausschließlich gehasht gespeichert wird
- Berechtigungsstufen **Nur lesen**, **Lesen & Schreiben** und **Vollzugriff**
- MCP-Werkzeuge für Bezugsobjekte, Tätigkeiten, Durchführungen, Historien und Fälligkeiten
- kein zusätzlicher Container und keine neue Datenbankmigration erforderlich
- Reverse-Proxy-Betrieb kann extern auf ausschließlich `/mcp` begrenzt werden
- Einrichtungsbeispiel für Reverse Proxy und Client: [`docs/MCP_SETUP.md`](docs/MCP_SETUP.md)

## Neu in 1.7.5

- eigenständige Bezugsobjekte mit Tätigkeiten-Untermenü
- schnelle Aktion „Heute erledigt“ bzw. bei Tieren „Heute gegeben“
- Wiederholung alle X Tage, Wochen, Monate oder Jahre ohne Pflicht-Starttermin
- reine Datums-Historie mit korrekter Sortierung und kompakter Intervallanzeige

## Aus 1.7.4.9 übernommen

- Wartungen und Tätigkeiten besitzen eine echte Durchführungshistorie mit frei nachtragbaren vergangenen Terminen;
- Abstände zwischen Durchführungen werden automatisch in Tagen berechnet, inklusive Durchschnitt sowie kürzestem und längstem Intervall;
- „Als durchgeführt markieren“ erzeugt automatisch einen Historieneintrag;
- Historieneinträge können Notiz, Kosten, Mess-/Zählerwert und Dateianhänge enthalten und nachträglich bearbeitet oder gelöscht werden;
- neue **Bezugsobjekte** lösen Wartungen von der reinen Asset-Logik: Geräte, Tiere, Fahrzeuge, Gebäude, Räume, Anlagen oder allgemeine Objekte können unabhängig vom technischen Inventar dokumentiert werden;
- dadurch kann beispielsweise `Penny → Impfung` oder `Kühlschrank → Filter wechseln` mit jeweils eigener Historie geführt werden;
- bestehende Asset-, Raum- und Elektro-Verknüpfungen bleiben kompatibel;
- Migration `0050` ergänzt Bezugsobjekte, Historienmetadaten und DB-basierte Anhänge.

## Neu in 1.7.4.8

- Monatsend-Ablesungen werden exakt am letzten Kalendertag fällig;
- Ablesungen vor dem gültigen Erinnerungsfenster erledigen die Aufgabe nicht mehr;
- verspätete Ablesungen können eine offene Aufgabe des Vormonats korrekt schließen;
- überfällige Monatsaufgaben bleiben über den Monatswechsel hinweg sichtbar;
- weitere Erinnerungstage werden als konkrete Kalendertage interpretiert;
- API und automatische Aufgaben verwenden dieselbe Berechnungslogik;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.4.7

- in der normalen Schaltschrankübersicht zeigt Mouse-over nur die direkt am gewählten Gerät angeschlossenen Hauptleitungen;
- Klick oder Antippen fixiert die hervorgehobene Verkabelung, ein weiterer Klick oder Escape hebt sie wieder auf;
- das gewählte Gerät und seine direkten Nachbarn werden hervorgehoben, nicht beteiligte Geräte dezent zurückgenommen;
- beim Überfahren einer Sicherung darf ihr eigener automatischer Kammschienenkontakt sichtbar werden, ohne sämtliche Kontakte der Schiene einzublenden;
- der vollständige Modus **Verkabelung** bleibt unverändert verfügbar;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.4.6

- manuelle Einspeisungen zu LS-/MCB-/RCBO-Schutzgeräten werden in der Verkabelungsansicht wieder dargestellt;
- ausgeblendet bleibt ausschließlich der nachgelagerte Zweig vom Schutzgerät zum einzelnen Stromkreis;
- automatische Einzelkontakte einer Kamm-/Sammelschiene bleiben zur Vermeidung unnötiger Mehrfachlinien verborgen;
- damit ist beispielsweise **Phasenverteilerblock → Sicherung Waschmaschine (L2)** sichtbar, während **Sicherung → Stromkreis Waschmaschine** ausgeblendet bleibt;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.


## Neu in 1.7.4.4

- Leitungen wählen ihre Anschlusspunkte oben oder unten jetzt dynamisch anhand der tatsächlichen Verlaufsrichtung;
- Verbindungen zu oberhalb liegenden Sammel- und Phasenschienen steigen direkt nach oben auf, statt zunächst nach unten zu laufen;
- von unten kommende Leitungen dürfen Geräte und Schienen sauber an der Unterseite erreichen;
- die schematische Hauptverkabelung bleibt innerhalb der Darstellung frei geroutet und hält die Adern weiterhin mit festem Abstand auseinander;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.4.3

- die starre Führung über Feldränder und obere Trassen wurde zurückgenommen;
- Hauptleitungen dürfen wieder innerhalb der Schrankdarstellung verlaufen;
- alle gültigen Hauptverbindungen werden unabhängig von ihrer Richtung dargestellt;
- die Adern einer mehradrigen Verbindung besitzen auf horizontalen und vertikalen Abschnitten einen festen Abstand von 8 Pixeln;
- mehrere Anschlüsse am selben Gerät werden auf getrennte Ports aufgefächert;
- einzelne Stromkreise sowie ihre LS-/RCBO-Abgänge bleiben ausgeblendet;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.4.2

- die Verkabelungsansicht ist auf die zentrale Hauptversorgung reduziert;
- schmale LS-/RCBO- und Ein-TE-Nebenabgänge werden nicht mehr gezeichnet;
- Leitungen verlaufen über seitliche Feldkorridore und obere Feldränder statt durch Gerätekarten;
- doppelte Hauptverbindungen werden zu einem visuellen Leitungsbund zusammengefasst;
- externe Anschlüsse werden nahe am zugehörigen Feld dargestellt;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.4

- die bisherige Umschaltung **Kompakt / Erweitert** wurde durch **Übersicht / Verkabelung** ersetzt;
- der neue Verkabelungsmodus zeichnet die gespeicherten Leiter direkt zwischen den sichtbaren DIN-Geräten und Schrankkomponenten;
- L1, L2, L3, N und PE werden mit klar unterscheidbaren, kontrastreichen Linien dargestellt;
- Hausanschlüsse erscheinen als Dreieck, externe Abgänge und Unterverteilungen als Kreis beziehungsweise Viereck;
- automatische Einzelkontakte einer Kamm-/Sammelschiene werden ausgeblendet; ihre Einspeisung wird je Leiter einmal dargestellt;
- N- und PE-Schienen bleiben in der Übersicht kompakt und zeigen dort keine ausführliche Verkabelungszusammenfassung mehr;
- die Detailansicht zeigt alle vor- und nachgelagerten Verbindungen mit Leiter, Verbindungsart und direktem Sprung in die Topologie;
- Phasen-Chips verwenden einen vollflächigen Hintergrund und weiße Schrift für besseren Kontrast im Dark Mode;
- Reihenzähler berücksichtigen Schutzgeräte, DIN-Assets und Schrankkomponenten gemeinsam; leere Null-Badges werden nicht mehr angezeigt;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.3

- getrennte Einspeisungen an demselben Ziel werden je Verbindung bewertet;
- eine direkte Verbindung **Netzanschluss → FI/RCD** mit ausschließlich `N`
  bleibt exakt `N`, auch wenn L1/L2/L3 über einen Phasenverteilerblock kommen;
- die Gesamtversorgung des FI/RCD wird weiterhin korrekt als Vereinigung aller
  eingehenden Leiter angezeigt;
- die irreführende Warnung „Gespeicherte Verbindung enthält abweichende Phasen“
  entfällt bei gültigen N-/PE-Einzelleiterwegen;
- im Verbindungsdialog können N und PE bewusst als eigenständige Leiterwege
  gewählt werden, ohne dass die Außenleiterautomatik sie erweitert;
- Alembic-Head bleibt `0049`; es ist keine neue Datenbankmigration erforderlich.

## Neu in 1.7.2

- N- und PE-Bereiche werden automatisch als echte elektrische Schrankkomponenten
  materialisiert und stehen damit als Quelle oder Ziel in der Topologie bereit;
- bestehende N-/PE-Bereiche werden durch Migration `0049` ohne Neuanlage
  nachgezogen;
- ein N-Schienenbereich erzeugt ausschließlich eine N-Schiene, ein
  PE-Schienenbereich ausschließlich eine PE-Schiene;
- reine N- und PE-Verbindungen erben keine Außenleiterphase mehr von FI/RCD,
  Sicherung, Stromkreis oder DIN-Asset;
- bei Auswahl einer N-Schiene wird nur N, bei Auswahl einer PE-Schiene nur PE
  gespeichert; eine direkte N-zu-PE-Verbindung wird abgelehnt;
- die Schrankansicht zeigt die erzeugten Schienen mit FI/RCD-Zuordnung und
  Verkabelungsstatus;
- Alembic-Head ist `0049`.

## Neu in 1.6.3.8

- Phasen-/Kammschienen und N-Schienen können jetzt FI/RCD-DIN-Assets aus
  derselben Verteilung auswählen;
- unterstützt werden unter anderem die Asset-Typen **FI-Schutzschalter** und
  **FI/LS-Schalter** sowie RCD-/RCBO-Bezeichnungen;
- historische FI/RCD-Schutzgeräte bleiben rückwärtskompatibel auswählbar;
- die Schienendetails zeigen den Namen des verknüpften FI-DIN-Geräts;
- ein zugeordneter FI kann erst nach dem Lösen der Schienenzuordnung aus dem
  Verteiler entfernt werden;
- Migration `0047` ergänzt den Asset-Verweis, ohne den bisherigen
  Schutzgeräteverweis zu entfernen.

## Neu in 1.6.3.6

- Asset-Typen mit fehlendem Nummernzähler können wieder Assets anlegen;
- insbesondere funktioniert **Smartes Relais / DIN-Schaltaktor** mit dem Produkt
  **Shelly Pro 1** wieder ohne HTTP-500-Fehler;
- Migration `0046` rekonstruiert fehlende oder veraltete Codezähler aus den
  vorhandenen DocOfHome-Codes;
- die Laufzeitlogik stellt fehlende Zähler zusätzlich selbstheilend wieder her.

## Neu in 1.6.3.5

- Phasen-/Kammschienen erzeugen automatische Kontakte zu **allen** vollständig
  überdeckten DIN-Geräten, nicht nur zu Schutzgeräte-Datensätzen;
- allgemeine DIN-Assets wie Stromstoßschalter, Schütze oder ältere als Asset
  platzierte Sicherungen erscheinen als Ziel der Schienenverbindung;
- bei einem vierpoligen FI/RCD werden L1, L2 und L3 verbunden, während der
  vierte Pol für N frei bleibt;
- Platzieren, Verschieben und Entfernen eines DIN-Geräts synchronisiert die
  abgeleiteten Verbindungen sofort;
- Migration `0045` repariert bestehende Verteilungen und legt fehlende Kontakte
  für vorhandene DIN-Asset-Platzierungen an.

## Neu in 1.6.3

- systemweite Integritätsprüfung des Elektro-Moduls und seiner Beziehungen;
- klare Trennung zwischen allgemeiner Sammelschiene und automatischer
  Phasen-/Kammschiene;
- autoritative, schreibgeschützte Kammschienen-Verbindungen zu vollständig
  überdeckten Schutzgeräten;
- gemeinsame Phasenberechnung für Schrankansicht, Topologie, Stromkreise und
  Smart-Meter-Messpunkte;
- konsistente FI-/N-/PE-Zuordnungen und korrigierte RCBO-Hinweise;
- Schutz vor Archivierung, Typwechsel oder Standortänderung bei aktiven
  elektrischen Abhängigkeiten;
- Migration `0043` zur Reparatur und Absicherung bestehender Elektro-Beziehungen.

## Neu in 1.6.2

- automatisch erzeugte, idempotente Monatsableseaufgaben;
- getrennte Dashboardkacheln für PV-Erzeugung und Netzeinspeisung;
- wirksame Phasen mit Warnung bei abweichenden Bestandsverbindungen;
- Haupt-/Unterverteilungen als strukturelle Behälter;
- Verteilerdosen ohne sichtbares TE-Raster;
- Kamm-/Phasenschienen als Overlay oberhalb oder unterhalb der Schutzgeräte;
- feste Repository- und Releaseinformationen in Anwendung und ZIP.

## Neu in 1.6.1

- separater, atomarer Zählerwechsel mit Schluss- und Startstand sowie sichtbarem
  letztem Zählerstand und OBIS-Hinweisen;
- mehrere PV-Zähler können gemeinsam für das Dashboard ausgewertet werden;
- konfigurierbare Online-Produktbildquellen;
- direkte elektrische Vor- und Nachfolger sowie gruppierte Phasenabgänge;
- einheitliche Erkennung aktiver Sicherungs-/Schutzgeräte;
- smarte Relais/DIN-Schaltaktoren und primäre Netzwerkschnittstellen.

## Neu in 1.6.0

- stabilerer Einrichtungsassistent mit schrittspezifischen Statusmeldungen,
  zuverlässiger Abschlussnavigation und manuellem Fallback;
- neue Backup-Namen mit `DocOfHome-backup-`; ältere
  `tectoryn-backup-`-Archive bleiben kompatibel;
- DuckDuckGo Images als primäre Online-Produktbildsuche mit Relevanzbewertung
  und Wikimedia Commons als Fallback;
- PC- und Tablet-orientierte Sicherungs-/Zählerschrankansicht mit kompakten
  Namen, optionalem Livewert beziehungsweise B16-Kurzangabe, Typfarben und
  Legende;
- Wasser- und Gaszähler werden nicht mehr als unplatzierte Elektrogeräte
  angeboten;
- Auslösecharakteristik und Nennstrom als Stammdaten und Asset-Override;
- empfohlener Standard-Asset-Typ **Stromstoßschalter** mit Spulenspannung,
  Spannungsart, Kontaktanzahl und Kontaktart;
- Smart-Meter-Messpunkte für CT-/Stromwandlerklemmen an vorhandenen
  Verkabelungen einschließlich eigener Home-Assistant-Entitäten;
- ausführlichere Handbucherklärung für Sammelschiene und Kammschiene.

## Betrieb und Sicherheitsmodell

DocOfHome ist für ein vertrauenswürdiges privates Netzwerk vorgesehen und darf
nicht ungeschützt aus dem Internet erreichbar sein. Änderungen und Arbeiten an
elektrischen Anlagen gehören in die Hände einer Elektrofachkraft. DocOfHome
dokumentiert den Bestand und ersetzt keine Planung, Prüfung oder
Sicherheitsberatung.

## Installation mit Docker Compose

```bash
cp .env.example .env
docker compose build
docker compose up -d
docker compose ps
```

DocOfHome ist standardmäßig unter `http://localhost:8088` erreichbar. Beim
Start werden die Alembic-Migrationen bis Head `0049` ausgeführt. Der persistente
Ordner `./data` enthält Datenbank, Uploads, Backups und Laufzeitdaten und gehört
nicht in ein Quellcode-Release.

## Update von 1.6.2 auf 1.6.3

1. Backup erstellen und den persistenten `data`-Ordner extern sichern.
2. Container stoppen: `docker compose down`.
3. 1.6.3 in einen neuen, sauberen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. `docker compose build --no-cache` und `docker compose up -d` ausführen.
6. Im Log das Upgrade `0042 -> 0043` kontrollieren.
7. Schrankansicht, automatische Kammschienen-Verbindungen, Stromkreise,
   Messpunkte und Topologie prüfen.

Bestehende manuelle Sammelschienen-Verbindungen bleiben erhalten. Eindeutige
Phasenschienen-Beziehungen und Messphasen werden durch Migration `0043`
konsistent repariert.

## Update von 1.6.3.1 auf 1.6.3.2

1. Persistenten `data`-Ordner sichern.
2. Container stoppen: `docker compose down`.
3. Version 1.6.3.2 in einen sauberen Ordner entpacken.
4. Image ohne Cache bauen: `docker compose build --no-cache`.
5. Container starten: `docker compose up -d`.
6. Browser mit `Strg+F5` vollständig aktualisieren.

Es ist keine neue Alembic-Migration erforderlich; Head bleibt `0044`. Beim
Speichern einer Kammschiene übermittelt die aktuelle Oberfläche die sichtbaren
Schutzgeräte ausdrücklich an den serverseitig validierten Kontaktabgleich.

## Update auf 1.7.4

1. Persistenten `data`-Ordner vollständig sichern.
2. Container stoppen: `docker compose down`.
3. Version 1.7.4 in einen sauberen Ordner entpacken.
4. Image ohne Cache bauen: `docker compose build --no-cache`.
5. Container starten: `docker compose up -d`.
6. Im Log das Upgrade bis Alembic-Head `0049` kontrollieren.
7. Browser mit **Strg+F5** aktualisieren.
8. Die getrennten Verbindungen **Phasenverteilerblock → FI/RCD** und
   **Netzanschluss → FI/RCD (N)** prüfen.

Für 1.7.4 ist keine zusätzliche Migration erforderlich. Migrationen `0046` und
`0047` übernehmen die Korrekturen aus 1.6.3.8.
Migration `0048` ergänzt den Funktionsumfang von 1.7 sowie die Referenz von
Stromkreisen auf aktuelle DIN-Schutzassets. Migration `0049` materialisiert
bestehende N- und PE-Schienenbereiche als verkabelbare Schrankkomponenten.
Historische Schutzgeräte bleiben rückwärtskompatibel.

## Entwicklung und Qualitätsprüfung

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/python -m pytest

cd ../frontend
npm ci
npm test
npm run build

cd ..
docker compose build --no-cache
```

## Weitere Informationen

- [Projektstatus](PROJECT_STATUS.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Release Notes 1.7.4](RELEASE_NOTES_1.7.4.md)
- [Release Notes 1.7.3](RELEASE_NOTES_1.7.3.md)
- [Release Notes 1.7.2](RELEASE_NOTES_1.7.2.md)
- [Release Notes 1.7.1](RELEASE_NOTES_1.7.1.md)
- [Migrationsanleitung](docs/MIGRATION_GUIDE_1.6.0.md)
- [Validierungsbericht](docs/VALIDATION_REPORT_1.6.0.md)
- [Bekannte Grenzen](docs/KNOWN_LIMITATIONS_1.6.0.md)

Lizenz: siehe [LICENSE](LICENSE).
