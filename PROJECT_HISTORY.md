# DocOfHome – Projekt-Historie

Diese Datei bündelt Changelog, Release Notes, Implementation Summaries, Release-Manifeste und Validierungsnotizen. Seit Version 1.7.14 werden keine separaten Dateien pro Release mehr angelegt.

## Historische Implementierungsnotizen

Stand: 23. Juli 2026

## Phase 0 – Baseline und Release-Struktur

- Quellstand `0.1.18-dev` und Übergabedokument vollständig geprüft.
- Bestehende Fehler vor Änderungen reproduziert: vier Backend-Fehler, drei fehlende
  Test-Fixtures, ein Frontendtest sowie SQLModel-/Alembic-Typabweichungen.
- Zentrale Datei `VERSION`, reproduzierbare `package-lock.json` und dynamische
  Backend-Versionsquelle ergänzt.
- Das Übergabedokument liegt als `docs/archive/CURRENT_STATUS_AND_BACKLOG_2026-07-23.md` vor.
- Baseline-Gates: FastAPI-Import und Frontendbuild erfolgreich; Fehler wurden in den
  folgenden Phasen behoben.

## Phase 1 – Kernmodule

- Migration `0024_release_core_enhancements`: Dashboardlayout, Primärzähler,
  Ablesepläne, Kalenderwartung, Switch-Port-Metadaten und globale Inventarnummer.
- Mobile Zählererfassung, responsive Monats-/Jahresdiagramme, Vollbild und
  barrierearme Detailbedienung.
- Dashboard mit persistentem Desktop-Editor, Hauptwasser-/Strom-/Gasvergleich,
  Drei-Tage-Fälligkeiten und Ableseerinnerungen.
- Kalenderregeln, globale Inventarnummern, Switch-Portgenerator, dokumentierter
  Netzwerkpfad und Frontansicht.
- Optionale read-only FRITZ!Box-Integration mit lokalem SSRF-Schutz und Mocktests.
- Logische Dienste/Container unter Host-Assets mit vollständig manueller Pflege.
- Bestehende Home-Assistant-, Suche-, Wiki-, VLAN-, Nextcloud- und Archivverträge
  durch die vollständige Regressionstestsuite abgedeckt.

API-Erweiterungen umfassen `/dashboard/config`, Verbrauchsvergleiche und
Ableseerinnerungen, `/work-items/upcoming`, serverseitige Inventarnummern,
Portvorschau/-erzeugung, dokumentierte Netzwerkpfade, Workloads und
`/fritzbox/devices`.

## Phase 2 – Portabilität und Historie

- Migration `0025_portability_workloads_audit`: Workloads und indizierte,
  unveränderliche Auditereignisse.
- Vollständiger JSON-Export mit Manifest und Secret-Ausschluss.
- Modulbezogener CSV-Export und rückimportierbare explizite Modulzuordnung.
- Schreibfreie Importvorschau, Konflikterkennung, Strategien `fail`/`skip` und
  transaktionaler Rollback.
- Filterbare Historie mit Redaction für Zugangsdaten, Konten und interne URLs.

## Phase 3 – Geführte Einrichtung

- Migration `0026_guided_setup_drafts`: fortsetzbare Entwürfe.
- Elf Schritte mit dynamischen optionalen Modulen, Dublettenprüfung und Vorschau.
- Bestehende Assets werden bevorzugt wiederverwendet.
- Asset, Netzwerk, Verbrauch, Verknüpfungen, Wartung, Notiz und Stromkreisbezug
  werden in einer Transaktion gespeichert; Fehler rollen die gesamte Kette zurück.

## Phase 4 – Stabilisierung

- Backend: Ruff und mypy bestanden; neue Release-, Integritäts- und
  FRITZ!Box-Tests bestanden.
- Frontend: Typprüfung und MDI-Prüfung bestanden; ein aktualisierter
  Integrations-Defaulttest wurde nach Ergänzung der FRITZ!Box angepasst.
- Fresh-DB und Alembic `upgrade head`/`check` bestanden.
- Der aus einem realen Containerstart gemeldete SQLite-Wiederanlauffehler in
  Migration 0024 ist behoben und mit einer persistenten 0023-Datenbank,
  verwaister Alembic-Arbeitstabelle und erhaltenem Nutzdatensatz regressionsgetestet.
- Vollständige finale Testläufe, Migrations-Roundtrip, Versions- und
  Brandingprüfung sowie mobile Browserprüfung bestanden.
- Die lokale Laufzeitprüfung mit frischem und persistentem Datenordner bestand.
  Ein echter Docker-Engine-Lauf war auf dem Host mangels Docker/Podman/WSL nicht
  verfügbar; Details stehen im Validierungsbericht.

Offene Risiken: keine bekannten Datenverlustpfade. Externe Integrationen bleiben
optional und ausschließlich lesend. DocOfHome 1.0 besitzt keine Benutzeranmeldung
und ist ausschließlich für ein vertrauenswürdiges privates Netzwerk bestimmt.

## 2026-07-23 – 1.0.0 Fixstand

Setup-Integrationen, FRITZ!Box TR-064, Gebäudestruktur-Assistent, Home-Assistant-Geräteanzeige, Immich-Bildauswahl, Abschlussnavigation und Browser-Favicon korrigiert beziehungsweise ergänzt.

## 2026-07-23 – 1.0.0 Fixstand 2

- dauerhafter Gebäudestruktur-Assistent unter Bereiche & Räume
- direkte Dashboard-Kachelsortierung mit explizitem Speichern/Abbrechen
- Suchfokus bei jedem Öffnen sowie `/` als browserunabhängige Alternative
- sichtbare FRITZ!Box-Hostliste mit MAC-Abgleich und bestätigter Zuordnung
- fachlich lesbare Änderungshistorie mit Objektbezug und einklappbaren RAW-Daten
- durchsuchbare Auswahl bestehender Assets im geführten Fachassistenten
- keine neue Migration; Alembic-Head bleibt 0026

## Phase 5 – Release 1.1.0 / Sprint 0038

- Zählertyp Netzeinspeisung und getrennte Zählerzuordnung für Netzbezug,
  PV-Erzeugung und Einspeisung ergänzt.
- Energie-Konfiguration für Netzanschluss, Netzbetreiber, Energieversorger,
  Zählpunkt und Anschlussleistung umgesetzt.
- PV-Quellen, Wechselrichter und Speicher als eigene Energiekomponenten mit
  optionaler Asset-Verknüpfung umgesetzt.
- Monatliche Bilanz für Hausverbrauch, Eigenverbrauch, Autarkiegrad und
  Eigenverbrauchsquote auf Basis des bestehenden Verbrauchsmoduls ergänzt.
- Elektro-Topologie von einer Ein-Quellen-Baumregel zu einem zyklusfreien
  Mehrquellen-DAG erweitert; alle eingehenden Verbindungen sind sichtbar und
  separat bearbeitbar.
- Statistikdiagramme je Serie skaliert, Primärzählerübernahme für Strom/Gas
  stabilisiert, Ableseerinnerungen in Wartung & Aufgaben integriert und
  visuelle Immich-Auswahl bei Ablesungen ergänzt.
- Migration `0027` auf kompletter leerer Kette, als direkter Upgradepfad von
  `0026` mit Nutzdaten, als Downgrade und als erneutes Upgrade lokal ausgeführt.
- Python-Syntax, eigenständig kompilierbare TypeScript-Module,
  Frontend-Logiktests, Version und Branding geprüft.
- Vollständige dependency-basierte Pytest-/Ruff-/mypy-/vue-tsc-/Vite-/Vitest-
  Läufe bleiben das Zielsystem-/CI-Gate, weil die benötigten Pakete nicht in der
  gelieferten ZIP enthalten waren und ausschließlich lokal gearbeitet wurde.

## Patch 1.1.1 – Ableseerinnerungen

- Intervallbasierte Fälligkeit aus den Verbrauchseinstellungen wird unter
  **Wartung & Aufgaben** auch für Zähler ohne Monatsplan angezeigt.
- Zähler ohne erste Ablesung werden sofort als fällig geführt.
- Die Erinnerungskarte bleibt auch ohne aktuelle Fälligkeit sichtbar.
- Integrations- und dependency-freie Regressionstests ergänzt.
- Keine neue Migration; Alembic-Head bleibt `0027_energy_balance`.

## Patch 1.1.2 – gesammelte Integrationskorrekturen

- Zähler-/Asset-/Ortszuordnung und HA-Livewerte ergänzt.
- N-/PE-Schienen, Zählerplatzierung und hierarchische Ortsauswahl umgesetzt.
- Netzanschluss als Topologiequelle und logische Netzwerkinterfaces ergänzt.
- Migration `0028` erstellt und geprüft.

## Patch 1.1.3 – Buildkorrektur

- Nicht verfügbares Icon `mdi-ground-wire` entfernt.
- PE-Schienen verwenden `mdi-earth`.
- Keine neue Migration; Alembic-Head bleibt `0028`.

## Phase 6 – Release 1.2.0

- Home-Assistant-Lazy-Loading, serverseitige Pagination und Filter umgesetzt.
- Mehrfachzuordnungen und Entitätsrollen pro Asset ergänzt.
- Allgemeine DIN-Hutschienengeräte mit TE-Platzierung und Livewerten ergänzt.
- N-/PE-Ebenen, Produktbildquellen, Asset-Serien, Inline-Labels und Navigation
  **Mehr** umgesetzt.
- Migration `0029` mit Upgrade-/Downgrade-Roundtrip geprüft.
- Vollständige dependency-basierte Test- und Buildläufe blieben mangels lokaler
  Abhängigkeiten beziehungsweise Docker als Zielsystem-/CI-Gate offen.

## Patch 1.2.1 – Status- und Dokumentationsbereinigung

- Veraltete Übergabe `0.1.18-dev` aus dem aktiven Projektplan entfernt und
  vollständig archiviert.
- `PROJECT_STATUS.md`, `ROADMAP.md` und ein neues zentrales Sprintregister als
  eindeutige Freigabequellen eingeführt.
- Historische Sprintverträge unverändert erhalten und ihre Statusbedeutung
  dokumentiert.
- Sprint 0039 „Über DocOfHome, Changelog, Impressum und Feedback“ als nicht
  freigegebenen Entwurf aufgenommen.
- Keine Code- oder Schemaänderung; Alembic-Head bleibt `0029`.

## Patch 1.2.2 – Frontend-Buildfix

- Zielsystemfehler der MDI-Prüfung nachvollzogen.
- Nicht verfügbares `mdi-label-plus-outline` an beiden Stellen im
  Asset-Labeldialog durch `mdi-tag-plus-outline` ersetzt.
- Version und aktuelle Releasedokumentation auf 1.2.2 angehoben.
- Keine API-, Schema- oder Migrationsänderung; Alembic-Head bleibt `0029`.

## Patch 1.2.3 – Frontend-TypeScript-Fix

- veraltetes `ConfigurationRead`-Fixture in `immichGallery.test.ts` ergänzt;
- `selectedImmichAlbumId` auf den benötigten Teiltyp `integrations` begrenzt;
- Version und aktuelle Releasedokumentation auf 1.2.3 angehoben;
- keine Migration, Alembic-Head bleibt `0029`.

## Patch 1.2.4 – Fehlerkorrekturen und robuste Schrank-/Netzwerkansichten

- Wikimedia-Suche um einen direkten Browser-Fallback mit Host-Allowlist,
  CORS-Parameter, Abbruch und Zeitlimits ergänzt;
- ausgewählte Browser-Treffer werden über den vorhandenen Upload-Endpunkt lokal
  gespeichert;
- HTTP-500-Ursache der Netzwerkübersicht behoben und Teilabfragen mit
  `Promise.allSettled` fehlertolerant gemacht;
- unbekannte Netzwerk-Enum-Werte erhalten neutrale Fallbacks;
- Schrankaufteilung für Unterverteilungen geöffnet, einfache Reihen direkt
  dargestellt und Feld-/Bereichsmodus für Unterverteilungen freigegeben;
- Migration `0030` mit Upgrade, Downgrade und erneutem Upgrade ergänzt;
- globale Benachrichtigungswarteschlange oberhalb von Dialogen eingeführt;
- mobile Zählerstandserfassung hält Eingaben bei Fehler und blockiert
  Mehrfachspeichern;
- Version und Releasedokumentation auf 1.2.4 angehoben.

## Release 1.3.0 – passive Schrankkomponenten

- Phasenverteilerblöcke, Sammelschienen, N-/PE-Schienen und Klemmen als
  Nicht-Asset-Objekte ergänzt;
- Verkabelungsendpunkt `cabinet_component` und Reihenplatzierungen ohne
  Bereichs-ID ergänzt;
- Migration `0031` mit Roundtrip-Prüfung erstellt.

## Patch 1.3.1 – DIN-Assets, Mehrfacheinspeisung und Verbrauchsstatus

- normale DIN-Assets direkt im TE-Raster dargestellt und in das gemeinsame
  Drag-and-drop aufgenommen;
- DIN-Breite am Asset oder Asset-Typ ergänzt, Produktpflicht entfernt;
- mehrere eingehende Verbindungen an Schrankkomponenten sichtbar gemacht;
- Leiterfluss an Schrankkomponenten gegen Konfiguration und aktive Einspeisungen
  validiert;
- laufenden Verbrauchsmonat auf **bis heute** begrenzt;
- Migration `0032` mit Upgrade-/Downgrade-Roundtrip geprüft;
- vollständige npm-, Backend- und Dockerläufe bleiben mangels verfügbarer
  Abhängigkeiten beziehungsweise Docker ein Zielsystem-Gate.

## Patch 1.3.2 – Reparatur Mehrfacheinspeisung

- Ursache auf Bestandsdatenbanken eingegrenzt: historischer Unique-Index auf
  `target_kind, target_id`;
- Migration `0033` entfernt den Index idempotent;
- isolierter Regressionstest erlaubt anschließend zwei Quellen auf einem
  Phasenverteilerblock;
- generische englische Integrity-Fehlermeldung durch deutsche Diagnose ersetzt.


## Release 1.4.0 – Sammelschienen, FI- und N-Gruppen

- Sammelschienen als TE-Overlay mit Startphase und wiederholter Phasenfolge
  ergänzt;
- FI/RCD-Zuordnung für Sammelschiene und N-Schiene ergänzt;
- wirksame FI-, N-Schienen- und Phasenzuordnung eines Schutzgeräts automatisch
  aus der Position ermittelt;
- manuelle Abweichungen als verständliche Warnungen dargestellt;
- Verteilungsansicht um Belegung, Kompakt-/Erweitert-Modus, Detailpanel und
  sichtbare Sammelschiene erweitert;
- Migration `0034` mit Upgrade-/Downgrade-/Re-Upgrade-Prüfung ergänzt;
- vollständige npm-, Backend- und Dockerläufe bleiben mangels verfügbarer
  Abhängigkeiten beziehungsweise Docker ein Zielsystem-Gate.

## Patch 1.4.1 – Info-Seite und direkter Ableseeinstieg

- zentrale Seite **Mehr → Über DocOfHome** mit Projektbeschreibung,
  Versionsanzeige und ausgelieferten Release Notes ergänzt;
- optionale Projektverweise, Lizenzhinweis und konfigurierbares Impressum
  ergänzt;
- standardmäßig deaktiviertes Feedbackformular mit ausdrücklicher Zustimmung
  für technische Metadaten und serverseitigem Nextcloud-Upload umgesetzt;
- Versionskachel vom Dashboard entfernt und bestehende Dashboard-Layouts ohne
  Verlust ihrer Reihenfolge normalisiert;
- direkten Dashboard-Button zur mobilen Zählerstandserfassung ergänzt;
- Migration `0035` mit Upgrade-/Downgrade-/Re-Upgrade-Prüfung ergänzt;
- vollständige npm-, Backend- und Dockerläufe bleiben mangels verfügbarer
  Abhängigkeiten beziehungsweise Docker ein Zielsystem-Gate.

## 1.7.14 – 2026-08-28

### Kurzüberblick

- Projekt- und GitHub-Struktur aufgeräumt; Release-Historie in dieser Datei zentralisiert.
- README als kompakte Projektseite mit Funktionsübersicht, Installation und Screenshots neu aufgebaut.
- Docker-Bereich um UGREEN-NAS/Docker-Engine-Synchronisierung erweitert: Containerimport, Status, Image, Ports, Netzwerke und Mounts.
- Manueller Docker-Refresh, konfigurierbares Aktualisierungsintervall, letzter erfolgreicher Abgleich und Fehlerstatus ergänzt.
- Dashboard-Erinnerungen dedupliziert und deutlich kompakter dargestellt.
- Netzwerk-IP-Abgleich ordnet bereits erkannte FRITZ!Box-Datensätze nachträglich per normalisierter MAC-Adresse zu.
- IP-Abgleich-Tabelle nach Status, Name, IP, MAC, Zuweisung und Quelle sortierbar.

### Technische Umsetzung

- Alembic-Migration `0054` ergänzt Docker-Sync-Einstellungen und Docker-Metadaten an Diensten/Containern.
- Docker Engine wird ausschließlich mit lesenden HTTP-GET-Anfragen über den lokalen Unix-Socket abgefragt.
- Docker-Container werden primär über die Container-ID, als Fallback über Host + Containername wiedererkannt.
- Manuelle DocOfHome-Felder wie Notizen, URLs und Reverse-Proxy-Zuordnung bleiben bei Docker-Synchronisation erhalten.
- Hintergrund-Scheduler prüft alle 30 Sekunden, ob das konfigurierte Aktualisierungsintervall fällig ist.
- Docker-Socket wird in `compose.yaml` in den DocOfHome-Container eingebunden.
- Die Versionsansicht in DocOfHome liest ab 1.7.14 diese zentrale `PROJECT_HISTORY.md`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.14",
  "base_version": "1.7.13.4",
  "built_on": "2026-08-28",
  "alembic_head": "0054",
  "database_migration_required": true,
  "release_reason": "Project cleanup, Docker Engine sync, compact reminders and network reconciliation"
}
```

### Validierung

Ausgeführt und erfolgreich:

- Versionskonsistenz, sichtbares Branding, gesammelte Fix-Verträge, Ableseerinnerungen und Releasevertrag `1.7.14`.
- Python-Syntaxprüfung per `compileall` für Backend, Migrationen, Tests und Prüfscripte.
- 195 TypeScript-/Vue-Skripteinheiten mit dem dependency-freien Syntaxcheck.
- Migrationsprüfungen `0030` bis `0054`; die älteren SQLite-Prüfungen inklusive Upgrade/Downgrade sowie die statischen Verträge der neueren Migrationen liefen erfolgreich.
- Elektro-/Phasenschienen-Regressionsverträge einschließlich Laufzeit-, Phasenmuster-, Autoritäts- und Breitenfallback-Prüfung.
- Projektbereinigung geprüft: keine separaten `CHANGELOG.md`, `RELEASE_NOTES_*`, `IMPLEMENTATION_SUMMARY_*`, `RELEASE_MANIFEST_*` oder `VALIDATION_*` mehr im Projektstamm.
- Zentrale `PROJECT_HISTORY.md` enthält alle 55 historisch in Einzeldateien vorkommenden Versionsstände.
- Neue Regressionstests für Docker-Import ohne Dubletten und für die nachträgliche MAC-Zuordnung im Netzwerk-IP-Abgleich ergänzt.

In dieser isolierten Buildumgebung nicht vollständig ausführbar:

- Backend-Pytest, Ruff, mypy und der vollständige Alembic-App-Lauf, weil `sqlmodel` und weitere Projektabhängigkeiten nicht installiert sind.
- Vitest, `vue-tsc` und Vite-Build, weil `frontend/node_modules` nicht vorhanden ist.

Der Docker-Build auf dem Zielsystem bleibt deshalb das finale Laufzeit-Gate.

## 1.7.13.4 – 2026-08-27

### Changelog

- Bilder, Dokumente und Dienste & Container (Docker) in die Modul-/Navigationsübersicht aufgenommen.
- Alle drei Bereiche können nun separat aktiviert und im Hauptmenü ein- oder ausgeblendet werden.
- Aktive ausgeblendete Bereiche erscheinen unter „Sonstiges“; deaktivierte direkte Routen werden gesperrt.
- Migration `0053` erhält für bestehende Installationen zunächst die bisherige Sichtbarkeit.

### Release Notes

## Vollständige Modul- und Menüsteuerung

- **Bilder** ist jetzt in **Einstellungen → Module und Navigation** verfügbar.
- **Dokumente** ist jetzt separat aktivierbar und im Hauptmenü ein-/ausblendbar.
- **Dienste & Container (Docker)** ist jetzt ebenfalls Bestandteil der Modulübersicht.
- Aktive, aber aus dem Hauptmenü ausgeblendete Einträge erscheinen wie die übrigen Module unter **Sonstiges**.
- Deaktivierte Module sind zusätzlich über ihre direkten Routen nicht mehr aufrufbar.

## Upgrade

Migration `0053` ergänzt die drei bisher fest sichtbaren Bereiche für bestehende Installationen automatisch in `enabled_modules_json` und `main_menu_modules_json`. Dadurch bleibt die bisherige Sichtbarkeit nach dem Update zunächst unverändert und kann anschließend in den Einstellungen angepasst werden.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.13.4",
  "base_version": "1.7.13",
  "built_on": "2026-08-27",
  "alembic_head": "0053",
  "database_migration_required": true,
  "release_reason": "Complete module/navigation controls for images, documents and workloads"
}
```

### Validierung

Stand: 27.08.2026

## Geprüfte Änderungen

- `images`, `documents` und `workloads` sind Frontend- und Backend-seitig gültige `ModuleKey`-Werte.
- Die Modulübersicht enthält **Bilder**, **Dokumente** und **Dienste & Container (Docker)**.
- Die drei Hauptmenüeinträge verwenden dieselbe Aktiv-/Hauptmenü-Logik wie die übrigen Module.
- Der Router blockiert die direkten Routen deaktivierter Module.
- Migration `0053` übernimmt bestehende Installationen ohne sichtbare Menüänderung und ergänzt beide Modul-Listen.

## Ausgeführte Prüfungen

- Versionskonsistenz 1.7.13.4: erfolgreich.
- Branding-Prüfung: erfolgreich.
- Releasevertrag 1.7.13.4: erfolgreich.
- Python-Syntax für Backend und Migrationen: erfolgreich.
- 195 TypeScript-/Vue-Skripteinheiten syntaktisch geprüft.
- Migration `0052`: statischer Vertragscheck erfolgreich.
- Migration `0053`: statischer Vertragscheck erfolgreich.
- Migration `0053`: Upgrade und Downgrade gegen SQLite mit vorhandenen Modulwerten erfolgreich geprüft.

## In dieser Umgebung nicht vollständig ausführbar

Der vollständige Pytest-/Mypy-/Ruff- und Vite-Testlauf konnte hier nicht ausgeführt werden,
weil insbesondere `sqlmodel` und `frontend/node_modules` in der isolierten Umgebung fehlen.
Die vorhandenen Projektprüfungen bleiben in `scripts/check.sh` hinterlegt.

Alembic-Head: `0053`

## 1.7.13.3 – 2026-08-27

### Changelog

- Rezeptbilder direkt per Kamera oder Dateiauswahl hochladen und lokal speichern.
- Rezeptbild aus Immich auswählen und lokal nach DocOfHome übernehmen.
- Manuelle Bild-URL nur noch unter „Erweitert“.
- Fehlendes Leerzeichen zwischen Mengen-/Einheitenangabe und Zutatenname behoben.

### Release Notes

Korrektur und Ausbau der Rezeptbilder sowie der Zutatenanzeige.

- Rezeptbilder werden im normalen Editor nicht mehr über ein URL-Feld gepflegt.
- Neue Aktionen **Foto aufnehmen**, **Bild auswählen** und **Aus Immich auswählen**.
- Aufgenommene und ausgewählte Dateien werden optimiert als WebP lokal unter dem persistenten DocOfHome-Datenverzeichnis gespeichert.
- Aus Immich gewählte Bilder werden beim Übernehmen nach DocOfHome kopiert; das Rezept bleibt damit unabhängig von einer späteren Immich-Verfügbarkeit.
- Eine manuelle Bild-URL bleibt nur noch unter **Erweitert** als Sonderfall verfügbar.
- Lokale Rezeptbild-Pfade werden von der Rezept-API ausdrücklich unterstützt.
- In der Rezeptdetail- und Druckansicht gibt es nun zuverlässig Abstand zwischen Mengenangabe/Einheit und Zutatenname, z. B. `130 g Salatgurke`.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.13.3",
  "base_version": "1.7.13",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "release_reason": "Recipe image camera/file/Immich workflow and ingredient spacing fix"
}
```

### Validierung

- Rezepteditor auf Kamera-, lokale Datei- und Immich-Auswahl umgestellt.
- Normales Bild-URL-Feld aus dem Hauptformular entfernt; manuelle URL nur noch unter „Erweitert“.
- Persistente lokale Speicherung für Rezeptbilder mit JPEG/PNG/WebP-Eingabe, Größenlimit und WebP-Optimierung ergänzt.
- Immich-Auswahl kopiert das gewählte Vorschaubild in den lokalen Rezeptbildspeicher.
- Rezept-Schema akzeptiert HTTP(S)-URLs sowie lokale Pfade beginnend mit `/`.
- Zutatenabstand in Detailansicht und Druckansicht explizit per Abstandsklasse abgesichert.
- Neue Frontend-Vertragstests und Backend-Tests für die Rezeptbild-Pfade ergänzt.
- Keine Datenbankmigration erforderlich; Alembic-Head bleibt `0052`.

## Ausgeführte Prüfungen

- Python-Syntaxprüfung für Backend und Tests: erfolgreich.
- DocOfHome-Versionskonsistenz: erfolgreich.
- Releasevertrag 1.7.13.3: erfolgreich.
- Branding, gesammelte Fix-Verträge, Ableseerinnerungen und Migration 0052 statisch geprüft: erfolgreich.
- 195 TypeScript-/Vue-Skripteinheiten syntaktisch geprüft: erfolgreich.
- Lokaler Rezeptbildspeicher mit erzeugtem JPEG → WebP und anschließendem Resolve praktisch geprüft: erfolgreich.

## In dieser Umgebung nicht vollständig ausführbar

- Vollständiger Backend-Pytest-Lauf nicht möglich, da `sqlmodel` in der isolierten Laufzeit nicht installiert ist.
- Vollständiger Frontend-Vitest-/Vue-Typecheck-/Vite-Build nicht möglich, da `frontend/node_modules` nicht im Quellpaket enthalten ist und externe Paketdownloads in dieser Umgebung nicht zur Verfügung stehen.

## 1.7.13.2 – 2026-08-27

### Changelog

- „Kochbuch“ aus dem aufgeklappten Wiki-Untermenü entfernt.
- Der eigenständige Kochbuch-Eintrag im Hauptmenü bleibt unverändert erhalten.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release Notes

Kleine Navigationskorrektur für das Kochbuch.

- Der zusätzliche Eintrag **Kochbuch** innerhalb des aufgeklappten Wiki-Menüs wurde entfernt.
- Der direkte **Kochbuch**-Eintrag im Hauptmenü bleibt bestehen und führt weiterhin zu `/wiki/kochbuch`.
- Aktivierung und Hauptmenü-Sichtbarkeit des Kochbuch-Moduls bleiben unverändert konfigurierbar.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.13.2",
  "base_version": "1.7.13",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "release_reason": "Navigation cleanup: remove duplicate cookbook entry from Wiki submenu"
}
```

### Validierung

- Doppelte Kochbuch-Navigation geprüft: Unterpunkt im Wiki-Menü entfernt.
- Eigenständiger Kochbuch-Hauptmenüeintrag bleibt in `moduleNavigation` erhalten.
- Route `/wiki/kochbuch` und Kochbuch-Modulkonfiguration bleiben unverändert.
- Keine Datenbankmigration erforderlich; Alembic-Head bleibt `0052`.

## 1.7.13.1 – 2026-08-27

### Changelog

- Rezept-Lesemodus, Editor und Kochmodus klar getrennt.
- Ablenkungsfreier, iPad-optimierter Vollbild-Kochmodus mit Portionsskalierung und optionalem Screen Wake Lock.
- Neuer Zutateneditor mit Autocomplete, Sortierfunktionen und Touch-tauglichen Aktionen.
- Responsive Rezeptansicht und größere Zubereitungskarten für Tablet und Desktop.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release Notes

Patch-Release für 1.7.13. Behebt den TypeScript-Buildfehler im neuen Kochmodus: Die Screen-Wake-Lock-API verwendet nun die nativen DOM-Typen, sodass `vue-tsc --noEmit` nicht mehr an einer inkompatiblen `Navigator`-Erweiterung scheitert.

Das Kochbuch erhält eine neu aufgebaute Rezeptoberfläche mit klar getrennten Ansichten für
Lesen, Bearbeiten und Kochen. Die normale Rezeptansicht bleibt in der DocOfHome-Oberfläche;
nur der Kochmodus wird als ablenkungsfreie Vollbildansicht dargestellt.

## Kochmodus

- Viewportfüllende, für iPad und Touch optimierte Kochansicht ohne DocOfHome-Navigation.
- Im Querformat Zutaten links und Zubereitung rechts; im Hochformat responsive Anordnung untereinander.
- Große Touch-Ziele zum Abhaken von Zutaten und Zubereitungsschritten.
- Portionswahl mit sofortiger Skalierung der Zutatenmengen.
- Optionaler Screen Wake Lock („Bildschirm nicht abschalten“) mit sauberem Browser-Fallback.
- Browser-Vollbild wird, sofern unterstützt, zusätzlich angefordert; die Kochansicht funktioniert auch ohne Fullscreen API.

## Rezeptansicht und Editor

- Lesemodus vom Bearbeiten getrennt und für Desktop sowie iPad neu gestaltet.
- Übersichtliche Rezeptinformationen, Bild, Zeiten, Zutaten und Zubereitungsschritte.
- Zutateneditor nach dem Bedienprinzip moderner Rezeptverwaltungen: Menge, Einheit, Zutat und Notiz in einer Zeile.
- Autocomplete-Vorschläge für vorhandene Zutaten, Kategorien und übliche bzw. bereits verwendete Einheiten.
- Zutaten per Drag-and-drop auf Desktop sowie über Touch-Aktionen auf iPad sortierbar.
- Zubereitungsschritte als größere Karten mit Sortieren- und Löschen-Aktionen.
- Leere Zutaten und Schritte werden vor dem Speichern bereinigt.

Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.13.1",
  "base_version": "1.7.13",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "release_reason": "Patch release for 1.7.13: fix TypeScript Wake Lock typing in cooking mode"
}
```

### Validierung

- Build-Fix: eigene `WakeLockNavigator`-Erweiterung entfernt; native `Navigator.wakeLock`-/`WakeLockSentinel`-Typen werden verwendet.
- Der zuvor gemeldete Fehler `TS2430` ist damit auf Quellcode-Ebene beseitigt.

- Kochbuch-Leseansicht, Bearbeitungsdialog und Kochmodus technisch getrennt.
- Kochmodus als viewportfüllende Overlay-Ansicht mit responsivem Quer-/Hochformat umgesetzt.
- Screen Wake Lock wird nur bei Browserunterstützung verwendet und bei Sichtbarkeitswechsel erneut angefordert.
- Vollbild-API ist optional; bei fehlender oder abgelehnter Unterstützung bleibt der Kochmodus vollständig nutzbar.
- Zutaten- und Schrittreihenfolge besitzt neben Desktop-Drag-and-drop explizite Touch-Aktionen.
- Portionsskalierung und Druckansicht bleiben erhalten.
- Rezeptdatenmodell und REST-API unverändert; keine Alembic-Migration erforderlich.
- Versions-, Branding-, Release- und TypeScript/Vue-Syntaxprüfungen wurden erfolgreich ausgeführt.
- `python -m compileall` für Backend, Tests und Release-Skripte wurde erfolgreich ausgeführt.
- Ein vollständiger `npm test`-/`npm run build`-Lauf war in der Erstellungsumgebung nicht möglich, weil die npm-Abhängigkeiten dort nicht vollständig aus dem Cache installiert werden konnten. Dieser CI-Lauf ist vor dem produktiven Deployment weiterhin empfohlen.

## Hotfix: TypeScript Wake Lock

- Docker-CI-Fehler TS2430 in `RecipeCookMode.vue` behoben.
- Eigene `WakeLockNavigator`-Deklaration entfernt und die nativen DOM-Typen `Navigator.wakeLock` / `WakeLockSentinel` aus TypeScript 5.8 verwendet.
- Lokaler vollständiger Frontend-Build in dieser Umgebung weiterhin nicht möglich, da die npm-Abhängigkeiten nicht vollständig installiert sind; der fehlerhafte Typkonflikt selbst ist beseitigt.

## 1.7.12 – 2026-08-27

### Changelog

- `save_recipe` veröffentlicht alle Rezeptfelder als explizites MCP-Eingabeschema.
- Generisches, für Clients nicht ausreichend beschreibbares `payload` entfernt.
- Stabile Speicherantwort mit `item` und `created`; unerwartete Fehler werden als Werkzeugfehler gemeldet.

### Release Notes

`save_recipe` besitzt nun ein vollständiges MCP-Schema mit einzelnen Feldern für Titel,
Zutaten, Schritte, Kategorie, Tags, Zeiten, Portionen, Notizen, URLs und Anhänge. Dadurch
können MCP-Clients einen korrekten Werkzeugaufruf erzeugen, ohne ein unbeschriebenes
`payload`-Objekt konstruieren zu müssen.

Die MCP-Berechtigung der geprüften Installation war bereits `admin`; die Korrektur betrifft
daher ausschließlich den Werkzeugvertrag. Keine Datenbankmigration.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.12",
  "base_version": "1.7.11",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "release_reason": "Explicit typed MCP schema for recipe saving"
}
```

### Validierung

- Laufende MCP-Einstellung geprüft: aktiviert, Token vorhanden, Berechtigung `admin`.
- Generisches Rezept-Payload durch explizite typisierte MCP-Parameter ersetzt.
- Such- und Speicherverträge für Rezepte statisch geprüft.
- Python-Syntax, Version, Branding und Releasevertrag geprüft.
- Release-ZIP mit `unzip -t` geprüft und SHA-256 ermittelt.

Ein realer MCP-Schreibtest benötigt die neu bereitgestellte Zielversion und wird nach dem
Deployment empfohlen. Vollständige CI-/Docker-Tests bleiben erforderlich.

## 1.7.11 – 2026-08-27

### Changelog

- `search_recipes` akzeptiert fehlende und explizit als `null` gesendete Filter.
- Stabile Suchantwort mit `items` und `count`, auch bei leerem Kochbuch.
- Regressionstest für den MCP-Rezeptsuchvertrag ergänzt.

### Release Notes

Diese Korrektur stabilisiert die MCP-Rezeptsuche bei einem leeren Kochbuch. Optionale
Suchfilter dürfen fehlen oder als `null` übertragen werden. Die Antwort besitzt stets die
Form `{"items": [...], "count": n}`. Bei leerem Bestand wird damit zuverlässig
`{"items": [], "count": 0}` geliefert und die anschließende Rezepterstellung kann fortfahren.

Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.11",
  "base_version": "1.7.10",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "release_reason": "Robust MCP recipe search for empty data and null filters"
}
```

### Validierung

- Laufende 1.7.10-REST-API bestätigt: `/api/v1/recipes` antwortet `200 OK` mit `[]`.
- Laufende Version über `/api/v1/health` als 1.7.10 bestätigt.
- Null-Filter und stabiles leeres Antwortobjekt für `search_recipes` implementiert.
- Python-Syntax, Versions-, Branding-, Release- und Regressionstestvertrag geprüft.
- Release-ZIP mit `unzip -t` geprüft und SHA-256 ermittelt.

Vollständige CI-/Docker-Tests sind für den Ziel-Build weiterhin erforderlich.

## 1.7.10 – 2026-08-27

### Changelog

- TypeScript-Syntax des MCP-Handbucheintrags korrigiert.
- Markdown-Inline-Code und nginx-Codeblock innerhalb des Template-Strings korrekt maskiert.
- Funktional identisch zu 1.7.9; keine Datenbankmigration.

### Release Notes

Version 1.7.10 ist das korrigierte Folge-Release zu 1.7.9. Der bereits veröffentlichte
Tag `v1.7.9` bleibt unverändert und reproduzierbar.

## Korrektur

- Unmaskierte Backticks im mehrzeiligen TypeScript-Handbuchtext wurden korrigiert.
- Inline-Code für `read`, `write` und `admin` bleibt als Markdown erhalten.
- Die nginx-Konfiguration wird als einklappbarer Markdown-Codeblock dargestellt.

Alle MCP-Funktionen aus 1.7.9 sind enthalten. Keine Datenbankmigration; Alembic-Head `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.10",
  "base_version": "1.7.9",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "release_reason": "Frontend build correction; published v1.7.9 tag remains immutable"
}
```

### Validierung

- Korrigierten 1.7.9-Quellstand als Basis verwendet.
- Versions-, Branding- und 1.7.10-Releasevertrag geprüft.
- MCP-Handbuch-Template-String auf unmaskierte innere Backticks geprüft.
- Python-Syntax der MCP-Backenddatei geprüft.
- Release-ZIP mit `unzip -t` geprüft und SHA-256 ermittelt.

Node.js/npm und pytest sind lokal nicht verfügbar; vollständige Frontend-, Backend- und
Docker-Testläufe müssen deshalb erneut durch CI ausgeführt werden.

## 1.7.9 – 2026-08-27

### Changelog

- MCP-Werkzeuge für Kochbuch, Wiki und verknüpfte Notizen.
- MCP-Werkzeuge für Assets, Orte, Assettypen, Produkte und Labels.
- MCP-Werkzeuge für Verbrauchszähler, Ablesungen und Verbrauchszusammenfassung.
- MCP-Werkzeuge für Netzwerkgeräte, Segmente, Schnittstellen, Adressen und Verbindungen.
- Einheitliches Berechtigungsmodell: Lesen, Schreiben und Löschen nur mit Vollzugriff.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release Notes

Version 1.7.9 erweitert MCP auf die ersten drei priorisierten Fachgruppen. Alle Funktionen
aus 1.7.8 bleiben erhalten.

## Wissen und Kochbuch

- Rezepte suchen und vollständig lesen, anlegen, ändern und löschen
- Wiki-Seiten suchen, lesen, anlegen, ändern und archivieren
- verknüpfte Notizen lesen, anlegen, ändern und löschen

## Assets, Orte und Stammdaten

Der Katalogzugriff unterstützt `asset`, `location`, `asset_type`, `product` und `label`.
Für jeden Bereich stehen Suche, Detailansicht, Anlegen, Ändern und kontrolliertes Archivieren
zur Verfügung. Es gelten dieselben Referenz- und Konfliktprüfungen wie in der Weboberfläche.

## Verbrauch und Netzwerk

- Verbrauchszusammenfassung, Zähler und Ablesungen lesen
- Zähler und Ablesungen anlegen, ändern und archivieren
- Netzwerkgeräte, Segmente, Schnittstellen, Adressen und Verbindungen verwalten

## Berechtigungen

- `read`: Suche und Lesen
- `write`: Anlegen und Ändern
- `admin`: Löschen und Archivieren

Keine Datenbankmigration. Der Alembic-Head bleibt `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.9",
  "base_version": "1.7.8",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "database_migration_required": false,
  "mcp_domains": [
    "cookbook",
    "wiki",
    "notes",
    "assets",
    "locations",
    "master_data",
    "consumption",
    "network"
  ]
}
```

### Validierung

## Ausgeführt

- DocOfHome 1.7.8 als unveränderte Release-Basis kopiert und auf 1.7.9 fortgeführt.
- Versionsvertrag, Branding, Syntax der erweiterten MCP-Datei und statischer Releasevertrag geprüft.
- Registrierungs- und Berechtigungsverträge für alle neuen MCP-Domänen ergänzt.
- Nach Docker-Lauf 33051360742 unmaskierte Backticks im TypeScript-Handbuch korrigiert und
  den vollständigen MCP-Template-String auf weitere unmaskierte Begrenzungszeichen geprüft.
- Release-ZIP nach Erstellung vollständig mit `unzip -t` geprüft und SHA-256 ermittelt.

## Einschränkungen

- Vollständige Backendtests sind lokal nicht ausführbar, da pytest und die Python-3.12-Projektabhängigkeiten fehlen.
- Frontendtests und Vite-Build sind lokal nicht ausführbar, da Node.js/npm fehlen.
- Fachliche MCP-Integrationstests benötigen eine migrierte Testdatenbank in der Ziel-/CI-Umgebung.

Diese Einschränkungen werden nicht als bestandene Tests ausgewiesen.

## 1.7.8 – 2026-08-27

### Changelog

- MCP zusätzlich über `/mcp/<token>`; `/mcp` mit Bearer-Header bleibt unverändert.
- Zentrale Clipboard-Hilfe mit sicherem Fallback.
- Lesbarere Markdown-Absätze, Listen, Inline-Code und einklappbare Codefenster mit Kopierbutton.
- Sticky Speicherleiste sowie Warnungen vor dem Verlassen ungespeicherter Einstellungen.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.

### Release Notes

Version 1.7.8 verbessert MCP-Zugang, Zwischenablage, Dokumentdarstellung und den Schutz
ungespeicherter Einstellungen. Alle Funktionen aus 1.7.7 bleiben erhalten.

## MCP für weitere Clients

- `/mcp` funktioniert unverändert mit `Authorization: Bearer <token>`.
- `/mcp/<token>` nutzt dieselbe Tokenprüfung, Berechtigung und denselben MCP-Server.
- Die Token-URL wird nur angezeigt, solange der Klartext-Token nach Erzeugung vorliegt.

## Robust kopieren

Kopieraktionen versuchen zuerst `navigator.clipboard.writeText` und verwenden bei fehlenden
Rechten oder unsicherem Kontext ein temporäres Textfeld mit `document.execCommand('copy')`.

## Lesbare Dokumentation

Absätze und Listen erhalten mehr Abstand. `Inline-Code` ist klar hervorgehoben. Mehrzeilige
Codeblöcke besitzen Sprache und Kopierbutton; längere Blöcke sind einklappbar.

```nginx
location ^~ /mcp/ {
    proxy_pass http://docofhome:8000;
}
```

## Einstellungen ohne Datenverlust

Eine sticky Leiste zeigt offene Änderungen und bietet **Verwerfen** sowie **Speichern**.
Interne Navigation, Neuladen, Schließen und Verlassen werden bei offenen Änderungen gewarnt.

Keine Datenbankmigration. Der Alembic-Head bleibt `0052`.

### Release-Manifest

```json
{
  "name": "DocOfHome",
  "version": "1.7.8",
  "base_version": "1.7.7",
  "built_on": "2026-08-27",
  "alembic_head": "0052",
  "source_archive_sha256": "a1906cce94931d01bd0fd8482a589a56c473ac29fc6c72fc3864b511d2881c5a",
  "database_migration_required": false,
  "features": [
    "mcp_token_path",
    "clipboard_fallback",
    "safe_markdown_code_windows",
    "settings_dirty_guard"
  ]
}
```

### Validierung

## Ausgeführt

- Original `DocOfHome-1.7.7.zip` mit SHA-256 `a1906cce94931d01bd0fd8482a589a56c473ac29fc6c72fc3864b511d2881c5a` als alleinige Basis verwendet.
- Versionsvertrag, Branding, Python-Syntax der geänderten Backenddateien und statischer 1.7.8-Releasevertrag geprüft.
- Release-ZIP nach Erstellung mit `unzip -t` geprüft und SHA-256 ermittelt.

## Einschränkungen

- Vollständige Backendtests waren lokal nicht ausführbar, da `pytest` und die Projektabhängigkeiten fehlen.
- Frontendtests, TypeScript-Prüfung und Vite-Build waren lokal nicht ausführbar, da keine Node.js-/npm-Laufzeit installiert ist.
- Ein echter MCP-Handshake benötigt eine konfigurierte Laufzeitdatenbank und wird in der Zielumgebung empfohlen.

Diese Einschränkungen werden nicht als bestandene Tests ausgewiesen.

## 1.7.7 – 2026-08-26

### Changelog

### Kochbuch und Navigation

- Eigenständiges Rezeptmodell mit strukturierten Zutaten und nummerierten Schritten.
- Rezeptübersicht, Suche nach Titel/Zutaten, Kategorien, Tags, Favoriten, Medienlinks,
  Duplizieren, Portionsumrechnung und Druckansicht.
- Module getrennt aktivierbar und im Hauptmenü platzierbar; dynamisches „Sonstiges“.
- Deaktivierte Module verlieren keine Daten.

### MCP und PWA

- MCP-Anleitung mit erprobter SWAG-Konfiguration in Handbuch und Runbook integriert.
- Direkter Dokumentationsbutton in den MCP-Einstellungen.
- Installierbarkeit als Progressive Web App mit zurückhaltendem, network-first Service Worker.
- Smart Home und Verbrauch nicht mehr als „In Vorbereitung“ gekennzeichnet.

### Technik

- Alembic-Head `0052` für Rezepte und getrennte Hauptmenü-Sichtbarkeit.

### Release Notes

Version 1.7.7 ergänzt ein strukturiertes Kochbuch, zentrale Modul- und
Navigationssteuerung, installierbare PWA-Unterstützung sowie die vollständige
MCP-/SWAG-Betriebsdokumentation im vorhandenen Handbuch und Runbook.

## Daten und Migration

- Migration `0052` legt die eigenständige Tabelle `recipes` an.
- Die vorhandene Modulauswahl wird um getrennte Hauptmenü-Sichtbarkeit ergänzt.
- Deaktivieren oder Ausblenden eines Moduls löscht keine Fachdaten.

## Bewusste Einschränkung

Eine gemeinsame Einkaufsliste ist noch nicht Bestandteil von 1.7.7. Sie wird als
spätere Erweiterung vorgesehen, weil Zusammenführung, Einheitenumrechnung,
Abhaken und mehrere Listen ein eigenes Datenmodell benötigen. Rezepte und Zutaten
sind bereits so strukturiert, dass diese Funktion später ohne Freitextmigration folgt.

### Implementation Summary

- Basis: unverändertes Release-ZIP DocOfHome 1.7.6.
- Migration 0052: Rezepte und getrennte Hauptmenü-Sichtbarkeit.
- Backend: validierte Rezept-CRUD-API einschließlich Suche und Duplizieren.
- Frontend: Kochbuch, Portionsumrechnung, Druckansicht und zentrale Navigation.
- Betrieb: integriertes MCP-/SWAG-Runbook und installierbare PWA.

### Validierung

## Ausgeführt

- Versionsvertrag und JSON-Manifest geprüft.
- Python-3.12-Syntax der neuen/angepassten Backend-, Schema- und Migrationsdateien geprüft.
- TypeScript-/Vue-Syntaxprüfung des vorhandenen Projekts ausgeführt.
- Statische Release- und Migrationsverträge für 1.7.7 geprüft.
- Release-ZIP nach Erstellung mit `unzip -t` geprüft und SHA-256 ermittelt.

## Einschränkungen

- Der vollständige Backend-Testlauf konnte in der lokalen Desktop-Umgebung nicht
  abgeschlossen werden, weil die isolierte Abhängigkeitsinstallation beim nativen
  `cryptography`-Build nicht innerhalb des verfügbaren Lauffensters fertig wurde.
- Frontend-Test und Vite-Produktionsbuild konnten nicht abgeschlossen werden, weil
  der Paketmanager einen Neuaufbau von `node_modules` verlangte und nach dem ersten
  Downloadlauf im eingeschränkten Netz nicht alle Tarballs erneut erreichbar waren.
- Ein echter SWAG-, Docker- und Chrome-PWA-Installationstest benötigt die Zielumgebung.

Diese Einschränkungen sind keine als bestanden deklarierten Tests. Das Dockerfile
behält die bestehenden Build-/Importprüfungen aus 1.7.6 bei.

## 1.7.6 – 2026-08-26

### Changelog

### MCP / ChatGPT

- MCP-Server direkt in das bestehende DocOfHome-Backend integriert.
- Streamable-HTTP-Endpunkt unter `/mcp`, kein zusätzlicher Container erforderlich.
- Aktivierung, öffentliche URL, Berechtigungsstufe und Token-Rotation in den Einstellungen.
- Bearer-Token mit 256 Bit Zufall; gespeichert wird ausschließlich der SHA-256-Hash.
- Lesende, schreibende und administrative MCP-Tools sind nach Berechtigungsstufe getrennt.
- Bezugsobjekte, Tätigkeiten, Durchführungen, Historien und Fälligkeiten sind über MCP nutzbar.

### Technik

- Offizielles MCP Python SDK 2.x als Runtime-Abhängigkeit.
- MCP und REST verwenden dieselben DocOfHome-Services.
- Reiner ASGI-Authentifizierungswrapper für Streamable HTTP.
- Keine Datenbankmigration; Alembic-Head bleibt `0051`.

### Release Notes

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

### Implementation Summary

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

### Validierung

Stand: 26.08.2026

## Erfolgreich in der Arbeitsumgebung

- Versionskonsistenz für `VERSION`, Backend, Frontend, Lockfile und `SOURCE_INFO.json`
- Python-Syntaxprüfung von Backend, Tests und Migrationen
- Branding-, gesammelte Regression- und Ableseerinnerungs-Verträge
- Releasevertrag 1.7.6 inklusive Erhalt der 1.7.5- und 1.7.4.9-Daten-/UX-Verträge
- Elektro-Integritäts-, Laufzeit- und Phasenschienen-Verträge
- 185 TypeScript-/Vue-Skripteinheiten über den dependency-freien Syntaxprüfer
- Migrationen 0030–0051; 0050 zusätzlich mit SQLite Upgrade/Backfill/BLOB/Downgrade
- Validierung der öffentlichen MCP-Adresse (`/mcp`, keine Credentials/Query/Fragmente)
- FastAPI/Starlette-Routingprobe: `/mcp` wird ohne Redirect an ein eingebettetes ASGI-App übergeben

## Neu enthaltene Tests

Backendtests decken ab:

- sichere MCP-Defaults (deaktiviert, nur lesen)
- Token-Erzeugung und ausschließlich gehashte Speicherung
- Verbot des Aktivierens ohne Token
- Token-Verifikation sowie `read`/`write`/`admin`-Grenzen

Frontendtests decken die separaten MCP-Einstellungs- und Token-Endpunkte ab.

## Umgebungsgrenze

In dieser isolierten Arbeitsumgebung sind `sqlmodel`, `ruff`, `mypy` und das neue
`mcp`-Python-Paket nicht installiert. Externe Paketdownloads sind per DNS blockiert.
Dadurch konnten der vollständige Backend-Pytest, Ruff/Mypy sowie ein echter Runtime-Aufruf
des MCP-SDK hier nicht ausgeführt werden. Die verwendete MCP-2.0-API wurde gegen die
aktuelle offizielle SDK-Dokumentation geprüft.

Der Docker-Build installiert `mcp>=2.0,<2.1` zusammen mit den übrigen Backend-Abhängigkeiten
und enthält weiterhin den vorhandenen Import-Smoketest `from app.main import app`. Ein normaler
online ausgeführter Docker-/GitHub-Build bricht daher bereits beim Image-Build ab, falls SDK,
FastAPI-Mount oder Backend-Import nicht kompatibel sein sollten.

Der vollständige Vue/Vite-Build konnte ebenfalls nicht erneut ausgeführt werden, weil das
hochgeladene Quell-ZIP erwartungsgemäß kein `node_modules` enthält und die benötigten npm-Pakete
nicht aus dem Netz geladen werden können. Der 1.7.5-Basisstand hatte diesen Build bereits
bestanden; die 1.7.6-Änderung der Oberfläche ist auf die MCP-Einstellungskarte begrenzt.

## 1.7.5 – 2026-08-25

### Changelog

### Bezugsobjekte / Tätigkeiten

- Tätigkeiten-Untermenü für Bezugsobjekte.
- Schnelle Aktionen „Heute erledigt“ und bei Tieren „Heute gegeben“.
- Wiederholungen alle X Tage, Wochen, Monate oder Jahre ohne initiale Pflicht-Fälligkeit.
- Historie arbeitet ausschließlich mit Kalendertagen und korrigiert zweistellige Jahreswerte.
- Nächste Fälligkeit basiert auf der letzten tatsächlichen Durchführung.

### Technik

- Migration `0051` repariert fehlerhafte zweistellige Jahreswerte und lockert die Wiederholungslogik.

### Release Notes

## Bezugsobjekte und Tätigkeiten

- Bezugsobjekte wie Tiere, Geräte, Fahrzeuge oder Räume besitzen ein eigenes Tätigkeiten-Untermenü.
- Tätigkeiten lassen sich ohne separaten initialen Fälligkeitstermin wiederholen.
- Wiederholungen werden als „alle X Tage/Wochen/Monate/Jahre“ erfasst.
- „Heute erledigt“ beziehungsweise bei Tieren „Heute gegeben“ protokolliert ohne zusätzlichen Dialog.
- „Anderes Datum / Details“ ergänzt optional Notiz, Kosten, Messwert und Anhänge.

## Datum und Historie

- Historien zeigen ausschließlich das Datum im Format TT.MM.JJJJ.
- Migration 0051 korrigiert versehentlich zweistellig gespeicherte Jahre (z. B. 0026 zu 2026).
- Sortierung und Abstände verwenden kalendarische Daten statt Uhrzeitdifferenzen.
- Die nächste Fälligkeit entsteht aus letzter tatsächlicher Durchführung plus Intervall.
- Die Historie ist kompakt; standardmäßig bleiben Anzahl und Durchschnitt sichtbar.

## Kompatibilität

- Migration 0050 und sämtliche 1.7.4.9-Daten bleiben erhalten.
- Klassische Aufgaben, technische Wartungen, Bezugsobjekte und Anhänge bleiben kompatibel.
- Ein Downgrade löscht keine Tätigkeits- oder Historiedaten.

### Validierung

Stand: 25.08.2026

## Erfolgreich

- Releasevertrag 1.7.5 und Versionskonsistenz
- Python-3.12-Kompilierung aller Backend- und Migrationsmodule
- Alembic-Neuaufbau von 0001 bis 0051 auf SQLite
- neue Backendtests für Wiederholung ohne Starttermin, Folgetermin und Datumssortierung: 2/2
- Vue-/TypeScript-Typprüfung
- Vite-Produktionsbuild (765 Module)
- Frontendtests: 170/175 erfolgreich

## Bestehende Regressionen aus der Basis 1.7.4.9

Fünf textbasierte Frontend-Vertragstests zu Elektroansicht und globalen Meldungen erwarten
ältere Quelltextfragmente, die im bereitgestellten 1.7.4.9-Stand bereits nicht mehr vorhanden
sind. Sie betreffen keine Datei der Bezugsobjekt-/Tätigkeiten-Änderung. Ein vorhandener
zeitabhängiger Backendtest zur Reaktivierung monatlicher Zähleraufgaben schlug ebenfalls fehl;
die neuen 1.7.5-Tests und die Migration sind davon unabhängig erfolgreich.

## Datenverträglichkeit

- Migration 0050 bleibt unverändert erhalten.
- Migration 0051 entfernt keine Tabellen oder Historieneinträge.
- Zweistellig gespeicherte Jahre werden von 00–99 in den Bereich 2000–2099 korrigiert.
- Wiederholungen ohne ersten Fälligkeitstermin sind nach der Migration zulässig.

## 1.7.4.9 – 2026-08-24

### Changelog

### Wartungs- und Tätigkeitshistorie

- Vergangene Durchführungen können mit frei wählbarem Datum nachgetragen werden.
- Das Erledigen einer Aufgabe oder Wartung erzeugt automatisch einen Historieneintrag.
- Pro Tätigkeit werden letzter und vorheriger Termin, letzter Abstand, Durchschnitt sowie kürzestes und längstes Intervall berechnet.
- Historieneinträge unterstützen Notizen, Kosten, Mess-/Zählerwerte und Dateianhänge.
- Historieneinträge und Anhänge können nachträglich bearbeitet beziehungsweise gelöscht werden.

### Bezugsobjekte

- Wartungen sind nicht mehr auf technische Assets angewiesen.
- Neue Bezugsobjekte unterstützen Geräte, Tiere, Fahrzeuge, Gebäude, Räume, Anlagen/Installationen sowie allgemeine und sonstige Objekte.
- Tätigkeiten eines Bezugsobjekts lassen sich gemeinsam filtern und aufrufen.
- Bestehende Verknüpfungen zu Assets, Orten und Elektroobjekten bleiben kompatibel.

### Technik

- Migration `0050` ergänzt `work_subjects`, die Zuordnung `work_items.subject_id`, detaillierte Historienfelder und DB-basierte Anhänge.
- Anhänge liegen als BLOB in SQLite und werden dadurch von den bestehenden Datenbank-Backups mitgesichert.

### Release Notes

Stand: 24.08.2026

Version 1.7.4.9 erweitert **Wartung & Aufgaben** um eine echte Tätigkeits- und
Wartungshistorie. Die Funktion ist bewusst nicht mehr ausschließlich an technische
Assets gebunden.

## Neue Bezugsobjekte

Für Tätigkeiten können wiederverwendbare Bezugsobjekte angelegt werden:

- Gerät
- Tier
- Fahrzeug
- Gebäude
- Raum
- Anlage / Installation
- Allgemein
- Sonstiges

Damit kann beispielsweise **Penny** als Tier geführt werden, ohne Penny als Asset
im technischen Inventar anzulegen. Unter diesem Bezugsobjekt können getrennte
Tätigkeiten wie **Impfung**, **Medikament**, **Entwurmung** oder weitere Vorgänge
angelegt werden.

Bestehende Verknüpfungen von Wartungen zu Assets, Orten, Verteilungen,
Schutzgeräten und Stromkreisen bleiben vollständig erhalten.

## Durchführungshistorie

Jede Aufgabe oder Wartung besitzt eine eigene Historie. Vergangene Durchführungen
können nachträglich ergänzt werden. Pro Durchführung stehen zur Verfügung:

- Durchführungsdatum und Uhrzeit
- Notiz
- Kosten und Währung
- Mess- oder Zählerwert mit Einheit
- Dateianhänge/Bilder bis 20 MB pro Datei

Beim normalen **Als durchgeführt markieren** wird automatisch ein Historieneintrag
erzeugt. Das Durchführungsdatum kann dabei optional abweichend gesetzt werden.

## Intervallauswertung

Aus den Durchführungen berechnet DocOfHome automatisch:

- letzte Durchführung
- vorherige Durchführung
- Tage seit der vorherigen Durchführung
- durchschnittlicher Abstand
- kürzester Abstand
- längster Abstand
- Anzahl der dokumentierten Durchführungen

Die Berechnung erfolgt immer innerhalb derselben Tätigkeit. Eine Medikamentengabe
beeinflusst daher beispielsweise nicht den Abstand zwischen zwei Impfungen.

## Anhänge und Backup

Anhänge werden in Version 1.7.4.9 direkt in der SQLite-Datenbank gespeichert.
Dadurch werden sie zusammen mit der Historie durch das bestehende DocOfHome-
Datenbankbackup erfasst und können nicht durch einen separat fehlenden Upload-
Ordner verwaisen.

## Datenbankmigration

Beim Start wird Migration `0050` ausgeführt. Sie:

- erstellt `work_subjects`;
- ergänzt `work_items.subject_id`;
- erweitert `work_item_events` um Durchführungsdatum, Kosten und Messwert;
- übernimmt für bestehende Events `created_at` als bisheriges Durchführungsdatum;
- erstellt `work_item_event_attachments` für DB-basierte Anhänge.

Vor dem Update wird wie gewohnt ein vollständiges DocOfHome-Backup empfohlen.

### Implementation Summary

## Datenmodell

- `WorkSubject` als eigenständige, wiederverwendbare Zuordnung außerhalb des Asset-Inventars;
- optionale `subject_id`-Zuordnung an `WorkItem` bei vollständiger Rückwärtskompatibilität zu bestehenden `target_type`/`target_id`-Verknüpfungen;
- `WorkItemEvent.occurred_at` als fachliches Durchführungsdatum;
- optionale Kosten-, Währungs-, Messwert- und Einheitsfelder;
- `WorkItemEventAttachment` mit Dateiinhalt als BLOB für backup-sichere Anhänge.

## API und Service

- CRUD für Bezugsobjekte;
- Historie lesen, rückwirkend anlegen, bearbeiten und löschen;
- Statistikberechnung aus chronologisch sortierten Durchführungen;
- Upload, Download und Löschen von Historienanhängen;
- bestehendes `complete` erzeugt weiterhin den Statusübergang und zusätzlich den detaillierten Historieneintrag;
- wiederkehrende Tagesintervalle verwenden das tatsächliche Durchführungsdatum als Basis für den nächsten Termin.

## Oberfläche

- Bezugsobjekte direkt unter „Wartung & Aufgaben“ verwalten und filtern;
- Tätigkeiten einem Bezugsobjekt zuordnen;
- eigener Historien-Dialog mit Kennzahlen und Zeitleiste;
- vergangene Durchführung nachtragen beziehungsweise bearbeiten;
- Kosten, Messwert und Anhang je Durchführung erfassen;
- bestehende objektgebundene Wartungen bleiben weiterhin nutzbar.

### Validierung

Stand: 24.08.2026

## Abgedeckte Verträge

- Versionskonsistenz `1.7.4.9` in VERSION, Backend, Frontend, Lockfile und SOURCE_INFO;
- Alembic-Head `0050`;
- allgemeine Bezugsobjekte einschließlich Typ `animal`;
- optionale `subject_id` an Work Items ohne Entfernung bestehender Zielverknüpfungen;
- rückwirkende Durchführungen über `occurred_at`;
- automatische Historie beim Erledigen;
- Intervallstatistik mit letztem, durchschnittlichem, kürzestem und längstem Abstand;
- Notiz, Kosten und Mess-/Zählerwert je Durchführung;
- DB-basierte Anhänge mit 20-MB-Grenze;
- Portabilität der Bezugsobjekte und Work-Item-Zuordnung;
- Regressionstest für `Penny → Impfung` mit 366 Tagen Abstand zwischen 03.02.2025 und 04.02.2026.

## In dieser Arbeitsumgebung ausgeführt

- Python-Syntaxprüfung der geänderten Backend-, API-, Modell-, Schema-, Service- und Migrationsdateien: erfolgreich;
- echter SQLite/Alembic-Test der Migration `0049 → 0050 → 0049`, einschließlich Backfill von `occurred_at` und BLOB-Anhang: erfolgreich;
- Pydantic-Vertragsprüfung für Bezugsobjekte, Kosten/Messwerte und Zuordnungsvalidierung: erfolgreich;
- dependency-freier Releasevertrag `scripts/check-release-1.7.4.9.py`: erfolgreich;
- dependency-freier TypeScript-Syntaxcheck über das vorhandene Projektskript: erfolgreich, sofern keine npm-Modulauflösung benötigt wird;
- JSON-Prüfung von SOURCE_INFO, package.json und package-lock.json: erfolgreich;
- finale Paketprüfung auf Version, Migrations-Head und erforderliche Dateien: erfolgreich vor Auslieferung.

## In dieser Arbeitsumgebung nicht vollständig ausführbar

- vollständiger Backend-Pytest sowie Ruff/mypy, da `sqlmodel` und weitere Projektabhängigkeiten nicht vollständig vorinstalliert sind; der direkte Alembic/SQLite-Migrationstest für `0050` wurde dagegen erfolgreich ausgeführt;
- Vue-Typecheck, Vitest und Vite-Build, da `frontend/node_modules` nicht im Quell-ZIP enthalten ist und der benötigte npm-Cache unvollständig ist. Ein Offline-Installationsversuch meldete fehlende Cache-Artefakte.

Die entsprechenden Projekt- und Regressionstests wurden im Quellstand ergänzt und sind für die normale CI-/Entwicklungsumgebung vorgesehen.

## 1.7.4.8 – 2026-08-24

### Changelog

### Zählerablesungen

- Monatsend-Fälligkeiten werden anhand des tatsächlichen letzten Kalendertags berechnet.
- Eine Ablesung gilt nur innerhalb des zur Fälligkeit gehörenden, nicht überlappenden Ablesefensters.
- Ablesungen vor dem Fenster schließen Monatsend-Aufgaben nicht mehr.
- Verspätete Ablesungen nach dem Monatswechsel können die offene Vormonatsaufgabe erledigen.
- Nicht erledigte Aufgaben bleiben nach Monatsende als überfällig erhalten.
- Weitere Erinnerungstage werden als konkrete Kalendertage und nicht als Tagesabstände ausgewertet.
- Reminder-API und automatischer Aufgabengenerator verwenden dieselben Datumshelfer.

### Technik

- Regressionstests für 30/31 Tage, Februar, Schaltjahr, frühe, fristgerechte und verspätete Ablesungen sowie zusätzliche Erinnerungstage.
- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

Stand: 24.08.2026

Version 1.7.4.8 korrigiert die automatische Zählerablesungslogik unter
**Wartung & Aufgaben**.

## Korrekturen

- **Monatsende:** Die Fälligkeit liegt immer auf dem tatsächlichen letzten
  Kalendertag (28/29/30/31).
- **Gültiges Ablesefenster:** Standardmäßig beginnt es drei Tage vor der
  Fälligkeit. Eine frühere Ablesung im selben Monat erledigt die Aufgabe nicht.
- **Verspätete Ablesung:** Das Fenster bleibt bis zum Beginn des nächsten
  Monatsfensters offen. So kann eine Ablesung nach dem Monatswechsel noch die
  Vormonatsaufgabe schließen, ohne die neue Aufgabe vorzeitig zu erledigen.
- **Überfälligkeit:** Offene Monatsaufgaben bleiben nach Monatsende sichtbar.
- **Weitere Erinnerungstage:** Werte wie `28` bedeuten den 28. Kalendertag des
  Monats und niemals „28 Tage vorher“.
- **Einheitlichkeit:** Reminder-API und automatischer Aufgabengenerator verwenden
  dieselben Datumshelfer und Ablesefenster.

## Update und Datenbank

- Vor dem Update wird weiterhin ein vollständiges Backup empfohlen.
- Es gibt keine Schemaänderung und keine neue Migration.
- Alembic-Head bleibt `0049`.

### Implementation Summary

Die Monatsablesungsregeln wurden in
`backend/app/services/consumption_reminders.py` zusammengeführt.

## Umsetzung

- kalenderkorrekte Fälligkeit für feste Ablesetage und den letzten Monatstag;
- gemeinsames, nicht überlappendes Ablesefenster je Monatsfälligkeit;
- Standardvorlauf von drei Tagen sowie zusätzliche konkrete Erinnerungstage;
- eindeutige Zuordnung verspäteter Ablesungen zur offenen Vormonatsfälligkeit;
- API-Rückblick auf eine offene Vormonatsfälligkeit;
- Aufgaben-Synchronisierung für aktuellen Monat, Vormonat und bereits offene
  ältere automatisch erzeugte Aufgaben;
- automatische Erledigung nur bei einer Ablesung innerhalb des gültigen Fensters;
- keine Frontend-Änderung erforderlich, da API- und Work-Item-Verträge stabil bleiben;
- keine Datenbankänderung; Alembic-Head `0049`.

### Validierung

Stand: 24.08.2026

## Abgedeckte Regressionen

- Monate mit 31 und 30 Tagen;
- Februar mit 28 Tagen und Schaltjahr mit 29 Tagen;
- zu frühe Ablesung am Monatsanfang;
- Ablesung am Beginn des gültigen Fensters;
- Ablesung exakt am Fälligkeitstag;
- verspätete Ablesung nach Monatswechsel;
- offene überfällige Aufgabe ohne gültige Ablesung;
- zusätzliche Erinnerungstage als Kalendertage;
- identische Kernlogik in Reminder-API und automatischem Aufgabengenerator.

## Ausgeführte Prüfungen

- Versionskonsistenz (`VERSION`, Backend, Frontend und Lockfile): erfolgreich;
- Releasevertrag `scripts/check-release-1.7.4.8.py`: erfolgreich;
- Branding- und gesammelte Releaseverträge: erfolgreich;
- JSON-Syntax von `SOURCE_INFO.json`, `package.json` und `package-lock.json`:
  erfolgreich;
- AST-Syntaxprüfung aller geänderten Python-Module und Tests: erfolgreich;
- dependency-freier Lauf der gemeinsamen Kalenderlogik für 31/30 Tage,
  Februar, Schaltjahr, frühe, fristgerechte und verspätete Ablesung sowie
  zusätzliche Kalendertage: erfolgreich;
- statische Prüfung, dass der letzte Migrationsstand `0049` ist: erfolgreich;
- finales ZIP erneut entpackt, Dateiliste und Dateiinhalte mit dem Paketstand
  verglichen: vor Bereitstellung erfolgreich durchgeführt.

## In dieser Umgebung nicht ausführbar

- vollständige Python-/Backend-Tests, Ruff und mypy;
- Alembic-Upgrade, Alembic-Check und ausführbare Migrationstests;
- Vitest, Vue-/TypeScript-Typprüfung und npm-Build.

Die bereitgestellte Umgebung enthält nur Apple Python 3.9 ohne pytest,
SQLModel, SQLAlchemy, Alembic, Pydantic, Ruff oder mypy. Das Projekt setzt
Python 3.13 voraus. Node und npm sowie `frontend/node_modules` sind ebenfalls
nicht vorhanden. Es wurden keine externen Pakete nachgeladen; alle lokal
möglichen Prüfungen wurden ausgeführt.

## Migration

Keine Schemaänderung. Der neueste Migrationsstand bleibt `0049`.

## 1.7.4.7 – 2026-07-29

### Changelog

### Interaktive Verkabelung

- Mouse-over in der normalen Übersicht blendet die direkten Hauptverbindungen des gewählten elektrischen Elements ein.
- Klick oder Antippen fixiert die Auswahl; erneuter Klick oder Escape löst sie.
- Gewähltes Gerät und direkte Nachbarn werden hervorgehoben, übrige Geräte dezent abgedunkelt.
- Der automatische Kammschienenkontakt einer konkret überfahrenen Sicherung kann gezielt erscheinen; die Gesamtansicht bleibt reduziert.
- Der vollständige Verkabelungsmodus bleibt erhalten.

### Technik

- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

Stand: 29.07.2026

Version 1.7.4.7 ergänzt die normale Schaltschrankübersicht um eine interaktive Verkabelungsanzeige. Die vollständige Leitungsansicht muss dadurch nicht dauerhaft geöffnet werden: Beim Überfahren eines elektrischen Elements werden nur dessen direkt angeschlossene Hauptleitungen sichtbar.

## Bedienung

- Mouse-over über Sicherung, FI/RCD, Zähler, DIN-Asset, Verteilerblock oder Schiene zeigt die direkt angeschlossenen Hauptverbindungen.
- Klick oder Antippen fixiert die Auswahl.
- Ein weiterer Klick auf dasselbe Element oder die Escape-Taste hebt die Fixierung auf.
- Das gewählte Element wird deutlich, seine direkten Nachbarn werden dezent hervorgehoben; nicht beteiligte Elemente treten optisch zurück.
- Im Modus **Verkabelung** wird weiterhin die vollständige Hauptverkabelung dargestellt.

## Darstellungsregeln

- Abgänge zu einzelnen Stromkreisen bleiben auch bei Mouse-over ausgeblendet.
- Manuelle Einspeisungen zu Sicherungen bleiben sichtbar.
- Beim Mouse-over einer konkreten Sicherung kann genau deren automatischer Kammschienenkontakt eingeblendet werden; beim Mouse-over der Kammschiene werden nicht sämtliche Einzelkontakte gezeichnet.
- FI/RCD behalten getrennte IN-/OUT-Anschlusspunkte.

## Technik

- reine Frontend-Erweiterung ohne Datenbankänderung;
- Alembic-Head bleibt `0049`.

### Implementation Summary

`CabinetWiringOverlay.vue` kann nun sowohl die vollständige Hauptverkabelung als auch einen interaktiven Fokusmodus darstellen.

## Umsetzung

- optionale Overlay-Eigenschaft `interactive`;
- delegierte Pointer- und Klick-Ereignisse auf den vorhandenen `data-electrical-endpoint-key`-Elementen;
- direkter Verbindungsfilter anhand des gewählten Endpunkts;
- Mouse-over für temporäre Auswahl, Klick/Antippen für Fixierung und Escape zum Zurücksetzen;
- dynamische Hervorhebung des gewählten Endpunkts und seiner direkten Nachbarn;
- selektive Anzeige eines automatischen Kammschienenkontakts nur beim Fokus auf die betreffende Sicherung;
- unveränderter vollständiger Verkabelungsmodus bei deaktivierter Interaktion.

### Validierung

- Versionsquellen auf `1.7.4.7` vereinheitlicht.
- Alembic-Head weiterhin `0049`.
- Overlay unterstützt vollständigen und interaktiven Fokusmodus.
- Mouse-over filtert auf direkte Verbindungen des Endpunkts.
- Klick/Antippen fixiert, erneuter Klick oder Escape löst die Auswahl.
- Stromkreis-Abgänge bleiben ausgeblendet.
- Manuelle Sicherungseinspeisungen bleiben sichtbar.
- Automatische Kammschienenkontakte werden nur für die konkret fokussierte Sicherung eingeblendet.
- FI/RCD-IN-/OUT-Darstellung und Aderabstände bleiben erhalten.

## 1.7.4.6 – 2026-07-29

### Changelog

### Verkabelungsansicht

- Manuelle Verbindungen zu LS-/MCB-/RCBO-Schutzgeräten werden wieder gezeichnet.
- Nur Verbindungen mit einem tatsächlichen Stromkreis-Endpunkt werden ausgeblendet.
- Die automatische Einzelverdrahtung einer Kamm-/Sammelschiene bleibt weiterhin reduziert.
- Dadurch bleiben Einspeisungen wie Phasenverteilerblock → Sicherung sichtbar, ohne die Grafik um Stromkreisabgänge zu erweitern.

### Technik

- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

Stand: 29.07.2026

Version 1.7.4.6 korrigiert den Darstellungsfilter der visuellen Schaltschrankverkabelung. In 1.7.4.5 wurden LS-/MCB-/RCBO-Endpunkte vollständig ausgeblendet. Dadurch fehlten auch gültige manuelle Einspeisungen zu einer Sicherung, obwohl sie in den Details korrekt dokumentiert waren.

## Korrektur

- Eine manuelle Einspeisung zu einem LS, MCB oder RCBO wird wieder dargestellt.
- Nur die Verbindung vom Schutzgerät zum einzelnen Stromkreis wird ausgeblendet.
- Automatische Einzelkontakte einer Kamm-/Sammelschiene bleiben weiterhin ausgeblendet, weil die Schieneneinspeisung bereits je Leiter dargestellt wird.
- Beispiel: **Phasenverteilerblock L1/L2/L3 → Sicherung Waschmaschine · L2** ist sichtbar.
- Der nachgelagerte Zweig **Sicherung Waschmaschine → Stromkreis Waschmaschine** bleibt unsichtbar.

## Technik

- keine neue Datenbankmigration;
- Alembic-Head bleibt `0049`.

### Implementation Summary

Der bisherige endpunktbezogene Filter wurde durch eine verbindungsbezogene Prüfung ersetzt.

## Vorher

Sobald ein Endpunkt den Gerätetyp `mcb` oder `rcbo` hatte, wurden sämtliche Verbindungen dieses Geräts ausgeblendet. Dadurch verschwand auch eine manuell dokumentierte Einspeisung vom Phasenverteilerblock zur Sicherung.

## Jetzt

- `isIndividualCircuitBranch()` blendet nur Verbindungen aus, deren Quelle oder Ziel tatsächlich ein Stromkreis-Endpunkt ist.
- Manuelle Einspeisungen zu LS-/MCB-/RCBO-Geräten bleiben sichtbar.
- Automatische Kammschienenkontakte werden weiterhin separat durch `isAutomaticBusbarContact()` reduziert.

### Validierung

- Versionsquellen auf `1.7.4.6` vereinheitlicht.
- Alembic-Head weiterhin `0049`.
- Endpunktweiter MCB-/RCBO-Filter entfernt.
- Verbindungsbezogene Stromkreisfilterung über `isIndividualCircuitBranch()` ergänzt.
- Manuelle Einspeisungen zu LS-/MCB-/RCBO-Geräten bleiben sichtbar.
- Schutzgerät-zu-Stromkreis-Verbindungen bleiben ausgeblendet.
- Automatische Kamm-/Sammelschienen-Einzelkontakte bleiben reduziert.

## 1.7.4.5 – 2026-07-29

### Release Notes

Stand: 29.07.2026

Version 1.7.4.5 korrigiert die räumliche und elektrische Aussagekraft der Schaltschrank-Verkabelung sowie die Kandidatenlisten in Unterverteilungen.

## Änderungen

- Der Hausanschluss wird am unteren Rand der Verkabelungsansicht dargestellt.
- Ein platzierter Zähler wird über sein verknüpftes Asset direkt am tatsächlichen Zählerfeld verankert.
- FI/RCD besitzen getrennte Anschlusszonen **IN** und **OUT**. Dadurch bleibt sichtbar, dass L und N das Gerät durchlaufen und eine nachgelagerte N-Schiene nicht direkt am Hausanschluss hängt.
- Die Listen „Noch nicht platzierte DIN-Assets“ und „Noch nicht platzierte Zähler“ berücksichtigen aktive Platzierungen in allen Verteilungen.
- Kandidaten werden auf den Ort der aktuellen Verteilung sowie Assets/Zähler ohne Ortszuordnung begrenzt.
- Die Topologie lädt aktive Schrankkomponenten aller Haupt- und Unterverteilungen zusätzlich nach. Dadurch stehen auch Kammschienen der aktuellen Unterverteilung als Quelle oder Ziel bereit.

## Technik

- Neue globale Leseendpunkte für aktive Asset- und Zählerplatzierungen.
- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Implementation Summary

- `CabinetWiringOverlay.vue`: Hausanschluss unten, Zähleranker am Zählerfeld, getrennte FI/RCD-Ports mit IN/OUT-Markern.
- `ElectricalDistributionLayoutPage.vue`: globale Platzierungslisten und Ortsfilter für DIN-Assets und Zähler.
- `ElectricalTopologyPage.vue`: Fallback-Nachladen aller aktiven Schrankkomponenten aus Haupt- und Unterverteilungen.
- Backend: globale Leseendpunkte für aktive Asset- und Zählerplatzierungen.

### Validierung

- Versionsquellen auf `1.7.4.5` vereinheitlicht.
- Alembic-Head weiterhin `0049`.
- Hausanschluss wird unten positioniert.
- Zählerkarten mit Asset-Verknüpfung besitzen einen elektrischen Endpunktanker.
- FI/RCD verwenden getrennte IN-/OUT-Anschlusszonen.
- Globale Asset- und Zählerplatzierungen werden geladen und nach aktuellem Verteilungsort gefiltert.
- Aktive Schrankkomponenten aller Verteilungen werden in die Endpunktauswahl eingebunden.

## 1.7.4.4 – 2026-07-29

### Changelog

### Verkabelungsansicht

- Anschlusspunkte werden für interne Geräte und Sammelschienen dynamisch an Ober- oder Unterseite gewählt.
- Aufsteigende Verbindungen zu oberhalb liegenden Sammel- oder Phasenschienen werden direkt nach oben geführt.
- Von unten kommende Leitungen können Komponenten und Schienen an der Unterkante erreichen.
- Die freie orthogonale Leitungsführung innerhalb der Schrankdarstellung bleibt erhalten; Adernabstände bleiben konstant.

### Technik

- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

Stand: 29.07.2026

Version 1.7.4.4 überarbeitet die Routing-Logik der visuellen Hauptverkabelung im Schaltschrank. Leitungen werden nicht mehr starr an Oberseiten geführt, sondern wählen ihre Anschlusspunkte an Geräten, Sicherungen und Sammelschienen passend zur tatsächlichen Verlaufsrichtung.

## Highlights

- dynamische Portwahl an internen Komponenten: oben bei von oben kommenden Leitungen, unten bei von unten kommenden Leitungen;
- direkte Aufwärtsführung zu oberhalb liegenden Sammel- und Phasenschienen ohne unnötige Schleife nach unten;
- saubere Unterseiten-Anbindung für Leitungen, die ein Gerät oder eine Schiene von unten erreichen;
- freie orthogonale Leitungsführung innerhalb der Schrankdarstellung bleibt erhalten;
- fester Abstand der einzelnen Adern bleibt erhalten;
- einzelne Stromkreise sowie ihre LS-/RCBO-Abgänge bleiben weiterhin ausgeblendet.

## Technik

- keine neue Datenbankmigration;
- Alembic-Head bleibt `0049`.

### Implementation Summary

Die Verkabelungslogik des Overlays wurde so angepasst, dass Anschlusspunkte an internen Geräten nicht mehr allein aus der Rolle als Quelle oder Ziel abgeleitet werden. Stattdessen entscheidet die relative Lage des Gegenpunkts, ob die Leitung an der Ober- oder Unterkante des Bauteils ansetzt.

## Umgesetzt

- `representedAnchor()` liefert jetzt die vollständige Geometrie eines sichtbaren Endpunkts.
- `choosePort()` wählt den Anschlusspunkt abhängig von der vertikalen Lage des Gegenpunkts.
- `orthogonalPath()` führt auf- und absteigende Leitungen direkt in die benötigte Richtung und hält dabei den vorhandenen Aderabstand bei.
- Bestehende Regeln zum Ausblenden einzelner Stromkreise und LS-/RCBO-Abgänge bleiben unverändert bestehen.

### Validierung

- Versionsquellen auf `1.7.4.4` vereinheitlicht.
- Alembic-Head weiterhin `0049`.
- Overlay wählt Anschlusspunkte oben oder unten abhängig von der Gegenposition.
- Aufsteigende Leitungen zu oberhalb liegenden Sammelschienen werden direkt nach oben geführt.
- Von unten kommende Leitungen enden an der Unterkante des Zielbauteils.
- Freie orthogonale Leitungsführung innerhalb der Schrankdarstellung bleibt aktiv.
- Fester Aderabstand von 8 Pixeln bleibt erhalten.
- Stromkreis- und LS-/RCBO-Nebenabgänge bleiben ausgeblendet.

## 1.7.4.3 – 2026-07-29

### Changelog

### Verkabelungsansicht

- Starre Feldrand- und Obertrassenführung entfernt.
- Freie orthogonale Leitungsführung innerhalb der Schrankdarstellung wiederhergestellt.
- Mehradrige Verbindungen erhalten auf allen Segmenten einen festen Leiterabstand.
- Gemeinsame Geräteanschlüsse werden auf getrennte Ports aufgefächert.
- Hauptverbindungen bleiben vollständig sichtbar; Stromkreis- und LS-/RCBO-Nebenabgänge bleiben ausgeblendet.

### Technik

- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

## Freie Leitungsführung mit sichtbarem Aderabstand

Version 1.7.4.3 nimmt die in 1.7.4.2 eingeführte starre Führung über Feldränder
und obere Trassen zurück. Hauptleitungen dürfen wieder innerhalb der
Schrankdarstellung verlaufen. Dadurch bleiben auch Verbindungen sichtbar, die
bei einer ausschließlichen Obertrassenführung abgeschnitten oder außerhalb des
sichtbaren Bereichs geführt wurden.

- Hauptverbindungen werden wieder mit der freien orthogonalen Grundlogik aus
  Version 1.7.4 geroutet.
- L1, L2, L3, N und PE erhalten auf horizontalen und vertikalen Segmenten einen
  festen Abstand von 8 Pixeln.
- Mehrere Verbindungen am selben Gerät werden an getrennten Anschlusspositionen
  aufgefächert.
- Deckungsgleiche Hauptverbindungen zwischen denselben Komponenten werden als
  gemeinsamer Leitungsweg mit der Vereinigung der Leiter dargestellt.
- Einzelne Stromkreise sowie ihre LS-/RCBO-Abgänge bleiben in der
  Schaltschrankgrafik ausgeblendet.
- Automatische Einzelkontakte einer Kamm-/Sammelschiene werden weiterhin nicht
  mehrfach gezeichnet.
- Topologie und Detailansichten bleiben vollständig und unverändert.

Es ist keine Datenbankmigration erforderlich. Der Alembic-Head bleibt `0049`.

### Implementation Summary

## Ausgangslage

Die schematische Feldrandführung aus 1.7.4.2 führte sämtliche feldübergreifenden
Leitungen über obere Korridore. Bei langen oder unterhalb liegenden Zielgeräten
konnten Wege dadurch abgeschnitten werden oder vollständig aus dem sichtbaren
Bereich verschwinden.

## Umsetzung

- Routing wieder auf frei innerhalb der Schrankfläche verlaufende orthogonale
  Pfade umgestellt.
- Leiterabstand wird nicht nur an den Endpunkten, sondern auch auf horizontalen
  und vertikalen Trassen berücksichtigt.
- Mehrere Verbindungen an einem Endpunkt werden anhand der Gegenposition
  sortiert und auf separate Anschlussports verteilt.
- Verbindungswege erhalten begrenzte Spurversätze, ohne an Feldränder gezwungen
  zu werden.
- Stromkreis-, MCB- und RCBO-Zweige bleiben aus der Hauptansicht entfernt.
- Keine Schemaänderung; Alembic-Head `0049`.

### Validierung

- Versionsquellen auf `1.7.4.3` vereinheitlicht.
- Alembic-Head weiterhin `0049`.
- Starre Feldrand- und Obertrassenfunktionen aus dem Overlay entfernt.
- Freie orthogonale Leitungsführung innerhalb der Schrankdarstellung geprüft.
- Fester Aderabstand von 8 Pixeln auf horizontalen und vertikalen Segmenten geprüft.
- Stromkreis- und LS-/RCBO-Nebenabgänge bleiben ausgeblendet.
- Mehrere Geräteanschlüsse werden auf getrennte Ports verteilt.
- Release-, TypeScript-Syntax-, Elektro- und Migrationsverträge erneut geprüft.

## 1.7.4.2 – 2026-07-29

### Changelog

### Verkabelungsansicht

- Nebenabgänge zu Stromkreisen sowie schmale LS-/RCBO-/Ein-TE-Geräte werden nicht mehr gezeichnet.
- Hauptleitungen werden an den Feldrändern gebündelt und zwischen Feldern über eine obere Trasse geführt.
- Doppelte Verbindungen zwischen denselben Hauptkomponenten erscheinen nur noch als ein Leitungsbund.
- Externe Knoten werden nahe am zugehörigen Feld platziert.
- Linienbreite und Kontur wurden reduziert.

### Technik

- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

## Schematische Hauptverkabelung

Version 1.7.4.2 reduziert die Verkabelungsansicht auf einen verständlichen
Versorgungsplan. Die vollständige gespeicherte Topologie bleibt unverändert und
ist weiterhin in den Detail- und Topologieansichten verfügbar.

### Änderungen

- einzelne Stromkreise sowie schmale LS-/RCBO- und Ein-TE-Abgänge werden in der
  Schrankgrafik nicht mehr gezeichnet;
- historische einpolige Sicherungen werden zusätzlich über ihre tatsächliche
  Kartenbreite als Nebenabgang erkannt;
- mehrere gleichgerichtete Verbindungsdatensätze zwischen denselben
  Hauptkomponenten werden zu einer visuellen Leitung gebündelt;
- Verbindungen innerhalb eines Feldes verlaufen über einen seitlichen
  Routing-Korridor;
- Verbindungen zwischen Feldern werden über die oberen Feldränder geführt;
- lange Leitungsabschnitte verlaufen damit nicht mehr mitten durch DIN-Geräte,
  Zählerfelder oder Gerätekarten;
- externe Ein- und Ausgänge werden nahe am zugehörigen Feld platziert, statt
  Leitungen bis zum unteren Ende der gesamten Seite zu verlängern;
- Linien und Konturen wurden zurückhaltender dimensioniert.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0049`.

### Implementation Summary

Der SVG-Verkabelungsmodus wurde von einem freien Leitungsrouting auf eine
schematische Korridorführung umgestellt. Hauptverbindungen werden an den
Feldrändern gebündelt; einzelne Stromkreisabgänge und schmale DIN-Nebenabgänge
werden nicht mehr dargestellt. Mehrfachdatensätze zwischen denselben
Hauptkomponenten ergeben nur noch einen visuellen Leitungsbund.

### Validierung

- Versionsquellen auf `1.7.4.2` vereinheitlicht.
- Releasevertrag für die reduzierte Hauptverkabelung ergänzt.
- TypeScript-/Vue-Syntaxprüfung ausgeführt.
- Verbindungen zu Stromkreisen, MCB/RCBO und schmalen Ein-TE-Geräten werden
  statisch ausgeschlossen.
- Doppelte Hauptverbindungen werden je Quell-/Zielpaar gebündelt.
- Feldinterne Leitungen nutzen seitliche Korridore.
- Feldübergreifende Leitungen nutzen die oberen Feldränder als Trasse.
- externe Knoten werden feldnah positioniert.
- Alembic-Head unverändert `0049`.

## 1.7.4.1 – 2026-07-29

### Release Notes

## Ziel

Version 1.7.4.1 überarbeitet die in 1.7.4 eingeführte visuelle
Verkabelungsansicht. Der Modus konzentriert sich nun auf die Hauptverteilung
und trennt parallele Leitungen klarer voneinander.

## Reduzierte Hauptverkabelung

Die Schrankansicht zeigt bewusst keine Verkabelung einzelner Stromkreise mehr.
Ausgeblendet werden:

- Stromkreis-Endpunkte;
- Verbindungen zu LS-/MCB- und FI/LS-/RCBO-Geräten einzelner Stromkreise;
- ältere als Sicherung modellierte Abzweige, wenn sie unmittelbar in einen
  Stromkreis führen.

Die vollständige Dokumentation bleibt in der Versorgungstopologie sowie in den
vor- und nachgelagerten Verbindungen der Detailansichten erhalten.

Sichtbar bleiben insbesondere Hausanschluss, Vorsicherungen, Zähler,
Phasenverteiler, FI/RCD, Sammel- und Kammschienen, N-/PE-Schienen,
Unterverteilungen und externe Hauptabgänge.

## Verbesserte Linienführung

- Verbindungen erhalten getrennte horizontale Kabelkanäle statt einer
  wiederholten Modulo-Zuordnung auf dieselben Spuren.
- Mehrere Verbindungen an demselben Gerät werden an getrennten Anschlusspunkten
  aufgefächert.
- Leiter einer mehradrigen Verbindung bleiben als paralleles Bündel sichtbar.
- Eine dunkle Kontur unter jeder Leitung trennt Kreuzungen und dicht
  nebeneinanderliegende Leiter optisch.
- Die Linienbreite wurde reduziert, damit Gerätebeschriftungen weniger verdeckt
  werden.

## Datenbank und Update

- Alembic-Head bleibt `0049`.
- Es ist keine neue Datenbankmigration erforderlich.
- Bestehende elektrische Verbindungen werden nicht verändert oder gelöscht;
  ausschließlich die Darstellung im Schrankmodus wurde angepasst.

### Validierung

## Automatisierte Prüfungen

- Versionsvertrag 1.7.4.1
- Releasevertrag 1.7.4.1
- TypeScript-/Vue-Skriptsyntax
- MDI-Iconprüfung
- bestehende Elektrointegritätsverträge
- bestehende Phasen-/Kammschienenverträge
- Migrationskette bis Alembic-Head 0049

## Neue Verträge

- Stromkreis-Endpunkte werden im Schrank-Overlay herausgefiltert.
- LS-/MCB- und FI/LS-/RCBO-Abgänge einzelner Stromkreise werden nicht gezeichnet.
- Direkte ältere Sicherung-zu-Stromkreis-Abzweige werden ebenfalls ausgeblendet.
- Mehrfachanschlüsse an einem Endpunkt erhalten getrennte Portpositionen.
- Verbindungen erhalten nach Routing-Kategorie getrennte Spuren.
- Eine Konturlinie trennt Leiter an Kreuzungen optisch.
- Die Bedienoberfläche weist ausdrücklich darauf hin, dass nur die
  Hauptverkabelung dargestellt wird.

## Manueller Smoke-Test

1. Verteilung mit mehreren Stromkreisen in der Ansicht „Verkabelung“ öffnen.
2. Prüfen, dass keine Leitung zu einzelnen LS-/RCBO-Stromkreisen erscheint.
3. Prüfen, dass Hausanschluss, Vorsicherung, Zähler, Phasenverteiler, FI/RCD,
   Schienen und Unterverteilungen weiterhin verbunden dargestellt werden.
4. Mehrere Leitungen an einem Hauptgerät prüfen: Anschlusspunkte und horizontale
   Spuren dürfen nicht exakt übereinanderliegen.
5. Kreuzende Leiter prüfen: Die dunkle Kontur muss die Leitungen voneinander
   abgrenzen.
6. Versorgungstopologie und Detaildrawer prüfen: ausgeblendete Stromkreiswege
   müssen dort weiterhin vollständig vorhanden sein.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0049`.

## Einschränkung der Build-Umgebung

Der vollständige Frontend-Build konnte in dieser Umgebung nicht ausgeführt
werden, weil der konfigurierte NPM-Spiegel benötigte Pakete mit HTTP 404 nicht
bereitstellte. Der geänderte Vue-Scriptblock wurde zusätzlich mit TypeScript
5.8.3 im Strict-Modus semantisch geprüft; die SFC-Template-Struktur wurde
separat geparst. Der reguläre Docker-Build muss `vue-tsc` und Vite nochmals
vollständig ausführen.

## 1.7.4 – 2026-07-29

### Changelog

### Schaltschrankdarstellung

- Die Umschaltung „Kompakt / Erweitert“ wurde durch „Übersicht / Verkabelung“ ersetzt.
- Ein neuer SVG-basierter Verkabelungsmodus verbindet sichtbare DIN-Geräte und Schrankkomponenten anhand der gespeicherten Topologie.
- L1, L2, L3, N und PE werden farblich unterschieden; Hausanschlüsse und externe Abgänge besitzen eigene Symbole.
- Automatische Einzelkontakte von Kamm-/Sammelschienen werden zugunsten einer Verbindung je Leiter nicht zusätzlich gezeichnet.
- N-/PE-Schienen zeigen in der kompakten Übersicht keine ausführliche Verkabelungszusammenfassung mehr.

### Details und Lesbarkeit

- Geräte-, Asset- und Komponentendetails listen vor- und nachgelagerte Verbindungen samt Leiter und Verbindungsart auf.
- Verbundene Endpunkte lassen sich direkt in der Topologie öffnen.
- Phasen-Chips wurden im Dark Mode kontrastreicher gestaltet.
- Reihenzähler erfassen alle sichtbaren Elemente, tragen eine verständliche Beschriftung und verschwinden bei leerer Reihe.

### Technik

- Neue Komponente `CabinetWiringOverlay.vue` berechnet die Linien dynamisch aus DOM-Positionen und Topologiedaten.
- Keine Datenbankmigration; Alembic-Head bleibt `0049`.

### Release Notes

## Ziel

Version 1.7.4 verbessert die Schaltschrankdarstellung und bündelt technische
Verkabelungsinformationen dort, wo sie benötigt werden: als visuelle Ebene in
der Übersicht und als strukturierte Liste in den Details.

## Neue Verkabelungsansicht

Die bisherige Umschaltung **Kompakt / Erweitert** wurde ersetzt durch:

- **Übersicht** – kompakte, aufgeräumte Schrankdarstellung;
- **Verkabelung** – dieselbe Schrankdarstellung mit dynamisch berechneten
  Leiterlinien.

Die Linien werden nicht statisch gespeichert. Sie werden aus der vorhandenen
elektrischen Topologie und den sichtbaren Positionen der DIN-Geräte,
Schrankkomponenten sowie Schienen erzeugt.

### Farblogik

- L1: Rot
- L2: Schwarz mit Kontrastkante
- L3: Hellgrau
- N: Blau
- PE: Grün beziehungsweise grün-gelb gestrichelt

### Symbole

- Der Netz-/Hausanschluss erscheint als Dreieck.
- Eine Leitung, die den aktuellen Verteiler verlässt, endet an einem Kreis.
- Eine nachgelagerte Verteilung beziehungsweise Unterverteilung wird als
  Viereck dargestellt.

Automatisch erzeugte Einzelkontakte einer Phasen-/Kammschiene zu jedem
überdeckten DIN-Gerät werden nicht zusätzlich als einzelne Linie gezeichnet.
Die Schiene selbst zeigt bereits die Verteilung; ihre Einspeisung wird je
Leiter einmal dargestellt.

## Kompakte Schienen

N- und PE-Schienen zeigen in der normalen Übersicht keine vollständige
Verkabelungszusammenfassung mehr. Name, Typ, Leiter und optionale FI-Zuordnung
bleiben sichtbar. Weitere Informationen stehen in der Detailansicht und in der
Verkabelungsansicht bereit.

## Vor- und nachgelagerte Verbindungen

Die Detailansichten von Schutzgeräten, DIN-Assets und Schrankkomponenten
enthalten jetzt zwei eigene Bereiche:

- **Vorgelagerte Verbindungen** – woher das Element versorgt wird;
- **Nachgelagerte Verbindungen** – welche Elemente weiter versorgt werden.

Jeder Eintrag zeigt verbundenes Objekt, Objekttyp, Verbindungsart, optionale
Leitungsdaten sowie die wirksamen Leiter. Der Eintrag öffnet den betreffenden
Endpunkt direkt in der Versorgungstopologie.

## Lesbarkeit und Reihenzähler

- L1/L2/L3/N/PE-Chips besitzen einen vollflächigen Hintergrund und eine deutlich
  kontrastierende weiße Schrift.
- Die bisher teilweise schwebende `0` war die Anzahl der Schutzgeräte und
  berücksichtigte DIN-Assets sowie Schrankkomponenten nicht. Der Zähler umfasst
  jetzt alle sichtbaren Elemente einer Reihe, ist als „Elemente“ beschriftet
  und wird bei leerer Reihe nicht angezeigt.

## Datenbank und Update

- Alembic-Head bleibt `0049`.
- Es ist keine neue Datenbankmigration erforderlich.
- Vor dem Update weiterhin den persistenten Datenordner und die Medien sichern.

### Implementation Summary

## Frontend

- Neue Komponente `frontend/src/components/CabinetWiringOverlay.vue`.
- Dynamische SVG-Pfade anhand von `data-electrical-endpoint-key` und den
  aktiven Topologieverbindungen.
- Automatische Neuberechnung bei Größenänderung, Scrollen und aktualisierter
  Topologie.
- Reduzierung automatischer Kamm-/Sammelschienenkontakte.
- Externe Markierungen für Hausanschluss und ausgehende Verbindungen.
- Detaildrawer um ein- und ausgehende Verbindungen erweitert.
- Inline-Verkabelungszusammenfassungen aus der kompakten Schrankansicht
  entfernt.
- Phasen-Chips in Schrank-, Topologie- und Versorgungswegansichten vereinheitlicht.
- Reihenzähler auf Schutzgeräte, Assets und Schrankkomponenten erweitert.

## Backend und Datenbank

Für 1.7.4 waren keine Schema- oder API-Erweiterungen notwendig. Die vorhandene
Topologieantwort enthält alle benötigten Endpunkte und Verbindungen.
Alembic-Head bleibt `0049`.

## Tests

- Neuer statischer Vertrag für visuelle Verkabelung und externe Symbole.
- Ergänzte Verträge für Detailverbindungen und vollständige Reihenzähler.
- Releasevertrag prüft Version, Alembic-Head, Darstellungsmodi, Busbar-Reduktion,
  Kontrastklassen und die Abwesenheit der alten erweiterten Ansicht.

### Validierung

## Automatisierte Prüfungen

- Versionsvertrag 1.7.4
- TypeScript-/Vue-Skriptsyntax
- MDI-Regressionsprüfung: gegenüber 1.7.3 wurden keine neuen Iconnamen eingeführt
- Releasevertrag 1.7.4
- bestehende Elektrointegritätsverträge
- bestehende Phasen-/Kammschienenverträge
- Migrationskette bis Alembic-Head 0049

## Neue statische Verträge

- Umschaltung `Übersicht / Verkabelung` vorhanden
- alte Option `Erweitert` entfernt
- N-/PE-Karten ohne eingebettete ausführliche Verkabelungszusammenfassung
- Detaildrawer enthält vor- und nachgelagerte Verbindungen
- vollständiger Reihenzähler ohne Null-Badge
- visuelle Leiterfarben L1/L2/L3/N/PE
- Dreieck für Hausanschluss
- Kreis/Viereck für externe Abgänge
- automatische Busbar-Einzelkontakte werden nicht mehrfach gezeichnet

## Manueller Smoke-Test

1. Schrankaufteilung öffnen und zwischen Übersicht und Verkabelung wechseln.
2. Prüfen, dass alle sichtbar platzierten Endpunkte korrekt verbunden werden.
3. Phasen-/Kammschiene prüfen: keine Linie pro einzelnem automatischem Kontakt.
4. Netzanschluss prüfen: Dreieck und passende Leiterlinien.
5. Abgang zu einer anderen Verteilung prüfen: externes Kreis-/Vierecksymbol.
6. DIN-Gerät öffnen und vor-/nachgelagerte Verbindungen prüfen.
7. N- und PE-Schiene in der Übersicht prüfen: keine ausführliche Einspeisungsbox.
8. L1/L2/L3-Chips im Dark Mode auf Lesbarkeit prüfen.
9. Leere Reihe prüfen: kein Badge. Belegte Reihe prüfen: vollständige Anzahl mit
   Beschriftung „Elemente“.

## In dieser Build-Umgebung nicht vollständig ausführbar

Der vollständige Lauf von `npm test` und `npm run build` war nicht möglich, weil
der konfigurierte NPM-Spiegel benötigte, im Lockfile festgelegte Pakete nicht
bereitstellte. Deshalb müssen `vue-tsc`, Vitest und der Vite-Produktionsbuild
beim Docker-Build beziehungsweise in der regulären CI erneut ausgeführt werden.
Die geänderten TypeScript-Skripte wurden zusätzlich mit TypeScript 5.8.3 und
lokalen Modulschnittstellen semantisch geprüft.

## 1.7.3 – 2026-07-28

### Changelog

### Getrennte Einspeisungen an FI/RCD und Schutzgeräten

- eine N- oder PE-Einzelleiterverbindung bleibt auf Verbindungsebene exakt N
  beziehungsweise PE;
- parallele L1/L2/L3-Einspeisungen am selben Ziel werden nur in der aggregierten
  Geräteversorgung zusammengeführt;
- die falsche Warnung über abweichende gespeicherte Phasen entfällt;
- Phasensperre und Phasenherkunft bleiben für reine N-/PE-Wege inaktiv;
- der Verbindungsdialog erzwingt L1/L2/L3 nur, wenn die bearbeitete Verbindung
  tatsächlich einen Außenleiter führt;
- Regressionstest für „Phasenverteilerblock → FI: L1/L2/L3“ plus
  „Netzanschluss → FI: N“ ergänzt.

### Release Notes

Version 1.7.3 korrigiert die Bewertung getrennter Einspeisungen an demselben
FI/RCD, Schutzgerät, DIN-Asset oder Stromkreis.

## Behobenes Fehlerbild

Eine fachlich gültige Dokumentation konnte bisher fälschlich als abweichend
markiert werden:

```text
Phasenverteilerblock → FI/RCD: L1, L2, L3
Netzanschluss        → FI/RCD: N
```

DocOfHome zeigte auf der separaten N-Verbindung dennoch die wirksamen Leiter
`L1, L2, L3, N` und meldete eine Abweichung. Ursache war, dass die Anwendung
die aggregierte Gesamtversorgung des Zielgeräts auf jede einzelne Verbindung
übertragen hat.

## Verhalten ab 1.7.3

- jede Verbindung wird anhand ihrer eigenen gespeicherten Leiter bewertet;
- eine N-Verbindung bleibt wirksam ausschließlich `N`;
- eine PE-Verbindung bleibt wirksam ausschließlich `PE`;
- parallele L1/L2/L3-Verbindungen bleiben unverändert;
- die Gesamtversorgung des FI/RCD enthält weiterhin die Vereinigung aller
  eingehenden Leiter, im Beispiel also `L1, L2, L3, N`;
- eine gültige N-/PE-Einzelleiterverbindung erhält keine Phasenwarnung und keine
  Außenleiter-Phasensperre;
- der Verbindungsdialog erweitert eine bewusste N-/PE-Auswahl nicht mehr um die
  Außenleiter eines parallelen Einspeisewegs.

## Datenbank

Alembic-Head: `0049`

Für diese Korrektur ist keine neue Migration erforderlich. Bestehende
Verbindungen werden beim Lesen unmittelbar korrekt bewertet. Ein erneutes
Speichern ist nicht erforderlich.

## Update

1. Persistenten `data`-Ordner sichern.
2. Container mit `docker compose down` stoppen.
3. Version 1.7.3 in einen neuen Ordner entpacken.
4. Image ohne Cache bauen: `docker compose build --no-cache`.
5. Container starten: `docker compose up -d`.
6. Browser mit `Strg+F5` aktualisieren.
7. Unter **Elektro → Versorgungswege** die separate N-Verbindung kontrollieren.

### Implementation Summary

## Backend

`ElectricalTopologyService` erkennt explizite Verbindungen, die ausschließlich
N und/oder PE führen. Für diese Verbindungen werden keine Außenleiteranforderungen
aus parallelen physischen Einspeisungen übernommen. Effektive Leiter,
Phasenherkunft, Sperrstatus und Warnungen bleiben verbindungsspezifisch.

Die aggregierte Versorgung eines Endpunkts wird unverändert aus allen
Eingangsverbindungen gebildet. Dadurch zeigt ein FI/RCD weiterhin insgesamt
L1/L2/L3/N, während die einzelne Neutralleiterverbindung ausschließlich N zeigt.

## Frontend

Die Außenleiterbindung wird nur aktiviert, wenn die aktuell bearbeitete
Verbindung tatsächlich L1, L2 oder L3 enthält oder eine automatisch verwaltete
Phasenschienenverbindung ist. Eine reine N-/PE-Auswahl kann daher angelegt und
bearbeitet werden, ohne automatisch um L1/L2/L3 erweitert zu werden.

## Migration

Keine neue Migration. Alembic-Head bleibt `0049`.

### Validierung

## Prüfumfang

- parallele L1/L2/L3- und N-Einspeisung an demselben FI/RCD;
- Verbindungsebene bleibt von der aggregierten Geräteversorgung getrennt;
- keine Abweichungswarnung bei einer gültigen N-only- oder PE-only-Verbindung;
- keine Außenleiter-Phasensperre für reine N-/PE-Wege;
- unveränderte Phasenvererbung für Verbindungen, die tatsächlich L1/L2/L3
  führen;
- Frontend erlaubt N-/PE-only auch bei einem Ziel mit bekannter Außenleiterphase;
- Version 1.7.3 bei unverändertem Alembic-Head `0049`.

## Ergänzte Regressionstests

Der Backend-Test bildet genau den gemeldeten Aufbau ab:

```text
Netzanschluss → Phasenverteilerblock: L1, L2, L3
Phasenverteilerblock → FI/RCD:       L1, L2, L3
Netzanschluss → FI/RCD:              N
```

Erwartet werden:

- N-Verbindung: `phases = [N]`;
- N-Verbindung: `effective_phases = [N]`;
- keine `phase_warnings`;
- keine `locked_line_phases`;
- aggregierte FI/RCD-Einspeisung: `L1, L2, L3, N`.

## In dieser Erstellungsumgebung ausgeführt

Erfolgreich ausgeführt wurden:

- Python-Kompilierung der geänderten Backend- und Testdateien;
- Release- und Versionsvertrag 1.7.3;
- statische Vue-/TypeScript-Syntaxprüfung;
- bestehende statische Elektro-, Phasenschienen- und Migrationsverträge bis
  Alembic-Head `0049`.

Der vollständige Backend-Pytest-Lauf konnte nicht ausgeführt werden, weil
`sqlmodel` im verfügbaren Python-Paketspiegel nicht bereitgestellt wurde. Der
vollständige Frontend-Build benötigt die NPM-Abhängigkeiten und muss beim
Docker-Build beziehungsweise in CI ausgeführt werden.

## 1.7.2 – 2026-07-28

### Changelog

### N-/PE-Schienen und getrennte Leiterverkabelung

- N- und PE-Bereiche werden als echte elektrische Schrankkomponenten angelegt
  und stehen als Quelle oder Ziel der Versorgungstopologie bereit;
- Migration `0049` materialisiert vorhandene aktive N-/PE-Bereiche ohne
  Neuanlage durch den Benutzer;
- die Schrankansicht erlaubt das Anlegen und Bearbeiten der jeweiligen Schiene
  direkt im passenden Bereich;
- N-Schienen erzwingen ausschließlich `N`, PE-Schienen ausschließlich `PE`;
- reine N-/PE-Verbindungen übernehmen keine L1/L2/L3-Phase von FI/RCD,
  Sicherung, Stromkreis oder DIN-Asset;
- zusätzliche N-/PE-Verbindungen bleiben auch bei vorhandener
  Phasen-/Kammschienenversorgung zulässig;
- direkte Verbindungen zwischen N- und PE-Schiene werden verhindert.

### Release Notes

Version 1.7.2 korrigiert die Modellierung und Verkabelung von Neutralleiter- und
Schutzleiterschienen in strukturierten Verteilungen.

## N- und PE-Schienen als Topologie-Endpunkte

Bereiche vom Typ **N-Schiene** und **PE-Schiene** waren bisher nur grafische
Schrankbereiche. Die Topologie konnte ausschließlich echte
`electrical_cabinet_components` als Quelle oder Ziel anbieten. Dadurch waren die
sichtbaren Bereiche im Verbindungsdialog nicht auswählbar.

Ab 1.7.2 gilt:

- ein neu angelegter N-Schienenbereich erzeugt automatisch eine echte
  N-Schrankkomponente mit Leiter `N`;
- ein neu angelegter PE-Schienenbereich erzeugt automatisch eine echte
  PE-Schrankkomponente mit Leiter `PE`;
- Migration `0049` ergänzt diese Komponenten für bereits vorhandene aktive
  N-/PE-Bereiche;
- die Komponenten erscheinen in **Elektro → Versorgungswege** sowohl als Quelle
  als auch als Ziel;
- die Schrankansicht zeigt die Schiene, ihren Verkabelungsstatus und bei
  N-Schienen die optionale FI/RCD-Zuordnung.

## Getrennte Leiterlogik

Reine N- und PE-Verbindungen werden nicht mehr von der Außenleiterlogik
überschrieben:

- FI/RCD → N-Schiene wird als reine N-Verbindung gespeichert;
- N-Schiene → Stromkreis oder DIN-Gerät bleibt ausschließlich N;
- PE-Schiene → Stromkreis oder DIN-Gerät bleibt ausschließlich PE;
- eine vorhandene L1/L2/L3-Versorgung des Zielgeräts blockiert eine zusätzliche
  N- oder PE-Verbindung nicht;
- eine direkte Verbindung zwischen N- und PE-Schiene wird abgelehnt;
- Phasenherkunft und Phasensperre bleiben für reine N-/PE-Verbindungen inaktiv.

## Migration

Alembic-Head: `0049`

Migrationskette:

```text
0045 → 0046 → 0047 → 0048 → 0049
```

Migration `0049` ist datenbewahrend. Beim Downgrade werden erzeugte
Schrankkomponenten bewusst nicht gelöscht, da sie bereits in 1.7.1 gültige
Objekte sind und nach dem Upgrade verkabelt worden sein können.

## Update

1. Persistenten `data`-Ordner sichern.
2. Container mit `docker compose down` stoppen.
3. Version 1.7.2 in einen neuen Ordner entpacken.
4. Image ohne Cache bauen: `docker compose build --no-cache`.
5. Container starten: `docker compose up -d`.
6. Im Log das Upgrade auf Alembic-Head `0049` kontrollieren.
7. Browser mit `Strg+F5` aktualisieren.
8. Unter **Elektro → Versorgungswege** prüfen, ob die vorhandenen N- und
   PE-Schienen angeboten werden.

### Validierung

## Prüfumfang

- Materialisierung bestehender N-/PE-Bereiche durch Migration `0049`;
- automatische Erzeugung bei neuen Schienenbereichen;
- Auswahl als Quelle und Ziel in der elektrischen Topologie;
- reine N-Verbindungen ohne erzwungene L1/L2/L3-Phase;
- reine PE-Verbindungen ohne erzwungene L1/L2/L3-Phase;
- Ablehnung einer direkten N-zu-PE-Schienenverbindung;
- unveränderte Phasen-/Kammschienenlogik für L1/L2/L3;
- Version und Alembic-Head `0049`.

## Automatisierte Verträge

- Python-Syntaxprüfung für Backend und Migrationen;
- statische Vue-/TypeScript-Syntaxprüfung;
- Releasevertrag `scripts/check-release-1.7.2.py`;
- Migrationstest `scripts/check-migration-0049.py`;
- Backend-Integrationstests für Schienenbereiche und N-/PE-Verbindungen;
- Frontend-Vertragstests für Schienenanlage und Leiterbeschränkung.

## Manuelle Smoke-Tests

1. Bestehende Installation von 1.7.1 auf 1.7.2 aktualisieren.
2. Einen vorhandenen N-Schienenbereich in **Versorgungswege** als Ziel auswählen.
3. FI/RCD → N-Schiene speichern; Ergebnis muss ausschließlich `N` enthalten.
4. N-Schiene → Stromkreis speichern; Ergebnis muss ausschließlich `N` enthalten.
5. PE-Schiene als Quelle auswählen und PE → Stromkreis speichern.
6. Prüfen, dass eine bestehende L1/L2/L3-Zuleitung am Stromkreis erhalten bleibt.
7. N-Schiene → PE-Schiene versuchen; Speichern muss mit verständlicher Meldung
   blockiert werden.

## In dieser Erstellungsumgebung ausgeführt

Erfolgreich ausgeführt wurden:

- Versions-, Branding-, Sammelfix-, Ablese-, Elektrointegritäts- und
  Phasenschienenverträge;
- Python-Kompilierung von Backend, Migrationen und Prüfscripten;
- statische Syntaxprüfung von 182 Vue-/TypeScript-Einheiten;
- isolierte Migrationsprüfungen der Revisionen `0030` bis `0049`;
- Upgrade- und Idempotenzprüfung der neuen Migration `0049`.

Der vollständige Backend-Pytest-Lauf war in dieser Umgebung nicht ausführbar,
weil das erforderliche Paket `sqlmodel` im verfügbaren Python-Paketspiegel nicht
bereitgestellt wurde. Der vollständige Frontend-Build konnte ebenfalls nicht
abgeschlossen werden, da die NPM-Abhängigkeitsinstallation am Paketspiegel
hängen blieb. Die dafür vorgesehenen Tests und Build-Schritte bleiben Bestandteil
von `scripts/check.sh` und müssen beim Docker-Build beziehungsweise in CI laufen.

## 1.7.1 – 2026-07-28

### Changelog

### Zusammenführung 1.6.3.8 und 1.7

- Korrekturen aus 1.6.3.6 bis 1.6.3.8 wurden per Drei-Wege-Abgleich in den
  1.7-Funktionsstand übernommen;
- fehlende Asset-Codezähler werden durch Migration `0046` und einen
  selbstheilenden Laufzeit-Fallback repariert;
- das aktuelle DIN-Asset-Modell ersetzt den alten Neuanlageweg für neue
  Hutschienengeräte, während historische Schutzgeräte kompatibel bleiben;
- FI/RCD- und FI/LS-DIN-Assets können Phasen-/Kammschienen und N-Schienen
  zugeordnet werden;
- die Stromkreis-Pflichtzuordnung unterstützt nun aktuelle DIN-Sicherungen,
  Leitungsschutzschalter und FI/LS/RCBO sowie historische Schutzgeräte;
- ein DIN-Asset kann nicht aus der Verteilung entfernt werden, solange es als
  FI/RCD einer Schiene oder als Endschutzgerät eines Stromkreises verknüpft ist;
- die frühere 1.7-Migration wurde wegen der offiziellen Migrationen `0046` und
  `0047` auf Revision `0048` verschoben.

### Release Notes

Version 1.7.1 führt die Korrekturen aus 1.6.3.6 bis 1.6.3.8 mit dem
Funktionsumfang von 1.7.0 zusammen. Die Zusammenführung wurde als
Drei-Wege-Abgleich gegen 1.6.3.5 durchgeführt, damit keine 1.7-Funktion durch
ältere Dateien überschrieben wird.

## Übernommen aus 1.6.3.6 bis 1.6.3.8

- fehlende und zu niedrige Asset-Codezähler werden per Migration `0046`
  repariert und bei der nächsten Asset-Erstellung zusätzlich selbstheilend
  rekonstruiert;
- neue Hutschienengeräte werden einheitlich als normale DIN-Assets platziert;
  der historische Schutzgerätepfad bleibt für Bestandsdaten erhalten;
- Phasen-/Kammschienen und N-Schienen können FI/RCD- und FI/LS-DIN-Assets
  derselben Verteilung referenzieren;
- eine Schiene speichert entweder den historischen FI/RCD-Verweis oder den
  aktuellen Asset-Verweis;
- ein verknüpftes FI/RCD-DIN-Asset kann erst nach dem Lösen der
  Schienenzuordnung entfernt werden.

## Anpassung der Stromkreis-Pflichtzuordnung

Die in 1.7.0 eingeführte Pflichtzuordnung zu einer konkreten Sicherung wurde an
das aktuelle DIN-Asset-Modell angepasst:

- Sicherungsautomaten, Leitungsschutzschalter, Sicherungen und FI/LS/RCBO aus
  aktiven DIN-Asset-Platzierungen werden als Schutzgerät angeboten;
- historische Sicherungs-, MCB- und RCBO-Datensätze bleiben auswählbar;
- ein eigenständiger FI/RCD ohne Überstromschutz bleibt für einzelne
  Stromkreise unzulässig;
- ein Schutzgerät kann nur einem aktiven Stromkreis zugeordnet werden;
- ein als Stromkreis-Schutzgerät verwendetes DIN-Asset kann nicht aus der
  Verteilung entfernt werden, bevor die Zuordnung geändert wurde;
- Typ, Nennwert, Position und erkennbare Außenleiter werden aus dem gewählten
  DIN-Gerät übernommen.

## Migrationen

Die Migrationskette lautet:

- `0046_repair_asset_code_counters`
- `0047_link_cabinet_rails_to_din_rcd_assets`
- `0048_release_1_7_1`

Die frühere 1.7.0-Migration mit der kollidierenden Revisionsnummer `0046` wurde
auf `0048` verschoben und erweitert. Sie enthält weiterhin Bilder,
Zähler-Capability, feste Portgeschwindigkeiten, Phasenherkunft und
IP-Abgleich sowie zusätzlich den Stromkreisverweis auf ein DIN-Asset.

## Korrektur des Frontend-Builds

- Das in der leeren IP-Übersicht verwendete, in `@mdi/font 7.4.47` nicht
  enthaltene Icon `mdi-ip-off-outline` wurde durch `mdi-ip-outline` ersetzt.
- Der vorangestellte MDI-Icon-Check blockiert den Docker-/Vite-Build dadurch
  nicht mehr.
- Die Asset-Erstellung auf der Smart-Home-Seite verwendet nun den zentralen
  `createEmptyAsset()`-Entwurf und enthält damit alle verpflichtenden
  Bildfelder des Typs `AssetWrite`.
- Home-Assistant-Asset-Entwürfe setzen `image_url`, `image_source` und
  `image_reference` explizit.
- Veraltete Test-Fixtures für `Asset`, `AssetType`, `ElectricalCircuit` und
  `ElectricalConnection` wurden an die erweiterten 1.7-Antwortverträge
  angepasst. Dadurch blockiert `vue-tsc --noEmit` den Build nicht mehr wegen
  fehlender Bild-, Schutzgeräte- oder Phasenherkunftsfelder.

## Update

1. Den vollständigen persistenten `data`-Ordner sichern.
2. Bestehende Container stoppen.
3. Version 1.7.1 in einen neuen, sauberen Ordner entpacken.
4. Image ohne Cache neu bauen.
5. Container starten und das Upgrade bis Alembic-Head `0048` kontrollieren.
6. Browser mit `Strg+F5` vollständig aktualisieren.
7. Stromkreise ohne konkrete Sicherungszuordnung in der Nacharbeitsliste prüfen.

Ein Downgrade sollte nur zusammen mit einem vor dem Update erstellten
Datenbank- und Medienbackup erfolgen.

### Implementation Summary

## Ausgangslage

Version 1.7.0 basierte auf 1.6.3.5. Zwischenzeitlich wurden in 1.6.3.6 bis
1.6.3.8 weitere Korrekturen veröffentlicht. 1.7.1 führt beide Entwicklungswege
zusammen.

## Wesentliche technische Entscheidungen

- Die offiziellen Migrationen `0046` und `0047` aus 1.6.3.8 bleiben unverändert
  erhalten.
- Die bisherige 1.7-Migration wurde auf `0048` verschoben.
- Neue Sicherungen und FI/LS werden als DIN-Assets behandelt.
- Historische `electrical_protective_devices` bleiben vollständig lesbar und
  auswählbar.
- Stromkreise speichern entweder `protective_device_id` oder
  `protective_device_asset_id`.
- Eine zentrale Klassifikation entscheidet, ob ein DIN-Asset ein FI/RCD oder
  ein zulässiges Endschutzgerät ist.
- Entfernen und Archivieren bleiben durch serverseitige Integritätsprüfungen
  abgesichert.

## Release

- Zielversion: `1.7.1`
- Alembic-Head: `0048`
- Grundlage: 1.6.3.8 plus Funktionsumfang 1.7.0

### Validierung

Stand: 28. Juli 2026

## Zusammenführung

Verglichen wurden die Quellstände 1.6.3.5, 1.6.3.8 und 1.7.0. Änderungen aus
1.6.3.8 wurden nicht pauschal über 1.7.0 kopiert, sondern datei- und
funktionsbezogen zusammengeführt. Besondere Konfliktbereiche waren
Versionsdateien, Migrationsnummern, Asset-Codevergabe, DIN-Geräte,
FI/RCD-Zuordnung und die Stromkreis-Sicherungsreferenz.

## Verbindliche Prüfpunkte

- Migrationskette ist linear: `0045 -> 0046 -> 0047 -> 0048`.
- Fehlende Asset-Codezähler werden repariert und zur Laufzeit rekonstruiert.
- FI/RCD-Schienenverweise unterstützen historische Geräte und aktuelle
  DIN-Assets, jedoch niemals gleichzeitig.
- Stromkreise akzeptieren genau eine Schutzgerätereferenz.
- Aktuelle DIN-Sicherungen, LS und FI/LS/RCBO sind auswählbar.
- Eigenständige FI/RCD und nicht schützende DIN-Geräte sind nicht auswählbar.
- Belegte Schutzgeräte werden gekennzeichnet und können nicht doppelt verwendet
  werden.
- Verknüpfte FI/RCD- oder Stromkreis-Schutzassets können nicht unbemerkt aus
  dem Verteiler entfernt werden.
- Sämtliche 1.7.0-Funktionen für Zähler, Netzwerk, Bilder, Switch-Ansicht,
  Aufgaben, Dialogmeldungen und Phasenherkunft bleiben enthalten.

## Durchgeführte technische Prüfungen

Erfolgreich ausgeführt wurden:

- Python-Syntaxprüfung für Backend, Tests und Prüfscripte über `compileall`;
- `python scripts/check-version.py`;
- `python scripts/check-release-1.7.1.py`;
- isolierte Upgrade-/Downgrade-Prüfungen der Migrationen `0046`, `0047` und `0048`;
- Syntaxprüfung von 182 TypeScript-/Vue-Skripteinheiten;
- Branding-, gesammelte Fix-, Elektrointegritäts-, Phasenschienen- und
  Ableseerinnerungs-Verträge;
- Prüfung auf doppelte Alembic-Revisionsnummern, Konfliktmarker und fehlerhafte
  Git-Diffs.
- Prüfung aller im Quelltext referenzierten MDI-Icons; die leere IP-Ansicht
  verwendet nun das in `@mdi/font 7.4.47` vorhandene `mdi-ip-outline`.
- Prüfung der nach 1.7 erweiterten Frontend-Typverträge: Asset-Entwürfe
  enthalten die verpflichtenden Bildfelder und Test-Fixtures bilden die
  vollständigen `Asset`-, `AssetType`-, `ElectricalCircuit`- und
  `ElectricalConnection`-Antworten ab.
- Die sieben von der Fehlermeldung betroffenen TypeScript-Produktions- und
  Testdateien wurden zusammen mit ihren lokalen Abhängigkeiten zusätzlich mit
  TypeScript 5.8.3 kompiliert; die gemeldeten Typfehler treten dabei nicht mehr
  auf. Für `vue` und `vitest` wurden wegen des nicht erreichbaren Paketspiegels
  ausschließlich temporäre Ambient-Deklarationen verwendet, die nicht im
  Release enthalten sind.

In der abgeschotteten Build-Umgebung konnten der vollständige Pytest-/Ruff-/Mypy-Lauf
sowie `npm test`, `vue-tsc` und der Vite-Produktionsbuild nicht ausgeführt werden,
weil die Python-Abhängigkeit `sqlmodel` nicht lokal vorhanden war und der interne
NPM-Spiegel die benötigten Pakete wiederholt mit HTTP 503 abwies. Die gemeldeten
`vue-tsc`-Fehler wurden vollständig anhand ihrer Typverträge korrigiert. Ein
erneuter realer Docker-/Vite-Build sowie ein Alembic-Upgrade gegen eine Kopie der
produktiven Datenbank bleiben vor dem produktiven Einsatz verpflichtend.

## Manuelle Smoke-Tests

Zusätzlich zu den Smoke-Tests aus dem Runbook:

1. DIN-Asset „Sicherungsautomat“ platzieren und einem Stromkreis zuordnen.
2. Dasselbe DIN-Asset bei einem zweiten Stromkreis auswählen: muss blockiert
   oder als belegt dargestellt werden.
3. Das zugeordnete DIN-Asset aus dem Schrank entfernen: muss blockiert werden.
4. Eigenständigen FI/RCD platzieren: darf nicht als Endschutzgerät eines
   einzelnen Stromkreises angeboten werden.
5. FI/RCD-DIN-Asset einer Phasen- oder N-Schiene zuordnen und anschließend
   Entfernung aus dem Schrank prüfen.
6. Ein Asset eines per Migration angelegten Typs ohne Codezähler erstellen und
   fortlaufenden DocOfHome-Code prüfen.

## 1.7.0 – 2026-07-28

### Release Notes

Version 1.7.0 konzentriert sich auf Datenintegrität in der Elektro-Dokumentation, einen nachvollziehbaren IP-Abgleich und kompaktere Bedienoberflächen.

## Wichtige Änderungen

- Jeder neue oder geänderte Stromkreis benötigt eine konkrete Sicherung, einen Leitungsschutzschalter oder einen RCBO aus derselben Verteilung. Bereits belegte einpolige Endschutzgeräte können nicht doppelt verwendet werden.
- Die Phase stammt vorrangig aus einer aktiven Kammschiene, danach aus einer aktiven Draht-/Kabelverbindung. Nur ohne physische Einspeisung bleibt eine manuelle Auswahl möglich.
- Zähler werden über eine stabile Capability erkannt. Bestehende Zählertypen werden bei der Migration automatisch gekennzeichnet.
- Monatliche Ableseaufgaben erscheinen im eingestellten Vorlauf, standardmäßig drei Tage vor Monatsende.
- Unter **Netzwerk > IP-Adressen** werden dokumentierte und durch die FRITZ!Box beobachtete Adressen getrennt angezeigt und über die MAC-Adresse abgeglichen.
- Switch-Fronten bleiben zweireihig; am Asset-Typ kann zwischen ungerade/gerade und einer Aufteilung in zwei fortlaufende Port-Hälften gewählt werden.
- Individuelle Bilder können direkt am Asset oder am Asset-Typ gespeichert werden. Uploads werden in WebP umgewandelt und verkleinert.

## Migration und Nacharbeit

Alembic-Migration `0046` ergänzt die neuen Felder und Tabellen. Bestehende Stromkreise ohne Schutzgerätezuordnung werden nicht blockiert, sondern in der Detailausgabe als fehlende Zuordnung kenntlich gemacht. Nach dem Update sollten diese Datensätze sowie gemeldete IP- und Phasenabweichungen geprüft werden.

Vor dem Update sind Datenbank und Medienordner zu sichern. Ein Schema-Downgrade ohne Wiederherstellung des passenden Backups ist nicht vorgesehen.

### Implementation Summary

Die Version setzt den freigegebenen Umfang des Runbooks 1.7 in der bestehenden FastAPI-/SQLModel- und Vue-/Vuetify-Anwendung um.

| Paket | Umsetzung |
| --- | --- |
| DOH-1701 | Globale Meldungen werden per Teleport oberhalb von Modalen gestapelt; feldbezogene Validierung bleibt erhalten. |
| DOH-1702 | Schnittstellengeschwindigkeit ist auf 100, 1000 und 2500 Mbit/s begrenzt und wird einheitlich formatiert. |
| DOH-1703 | Dokumentierte und erkannte IPs werden getrennt gespeichert, per normalisierter MAC abgeglichen und mit Status, Konflikten, Übernahme, Ignorieren und Audit dargestellt. |
| DOH-1704 | FRITZ!Box-Geräte werden numerisch nach IPv4-Adresse sortiert; ungültige Adressen stehen am Ende. |
| DOH-1705 | Hostname-Fehler nennen unzulässige Unterstriche konkret und schlagen Bindestriche vor. |
| DOH-1706 | Switch-Fronten bleiben zweireihig, horizontal scrollbar und unterstützen konfigurierbare physische Portmuster. |
| DOH-1707 | Zähler werden über die stabile Capability `is_meter` erkannt; bestehende Zählertypen werden migriert. |
| DOH-1708 | Monatsend-Ablesungen erscheinen im konfigurierten Vorlauf oder standardmäßig drei Tage vorher und bleiben periodengenau/idempotent. |
| DOH-1709 | Gerätekarten wurden verdichtet und für Desktop, Tablet und Mobil neu gerastert. |
| DOH-1710 | Einzelne Assets und Asset-Typen erhalten eigene JPEG-/PNG-/WebP-Bilder mit Optimierung, Entfernen und Fallback. |
| DOH-1711 | Neue/geänderte Stromkreise benötigen ein aktives, platziertes, geeignetes und nicht anderweitig belegtes Endschutzgerät derselben Verteilung. |
| DOH-1712 | Die Phasenherkunft wird als Kammschiene, Draht oder manuell geführt; reale Verbindungen haben Vorrang und veraltete Schienensperren werden repariert. |

## Release-Technik

- Zielversion: `1.7.0`
- Alembic-Head: `0046`
- Migration mit Upgrade-/Downgrade-Prüfung
- Regressionstests für die neuen Kernregeln ergänzt
- Statische Python-, Vue-/TypeScript-, JSON- und TOML-Prüfungen erfolgreich

Die noch vorgeschriebenen produktionsnahen Smoke-Tests und der vollständige CI-Lauf sind in einer Umgebung mit allen Entwicklungsabhängigkeiten durchzuführen. Details stehen in `VALIDATION_1.7.0.md`.

### Validierung

## Durchgeführte Prüfungen

- alle Python-Dateien in Backend, Migrationen und Tests erfolgreich kompiliert;
- Python-AST, `package.json`, `package-lock.json` und `pyproject.toml` erfolgreich geparst;
- TypeScript-Dateien und die TypeScript-Blöcke aller Vue-Komponenten syntaktisch transpiliert;
- Versionsvertrag und statischer Releasevertrag `scripts/check-release-1.7.0.py` erfolgreich;
- Migration `0046` auf einem synthetischen 1.6.x-Schema einschließlich Upgrade und Downgrade ausgeführt;
- vorhandene Tests an die verpflichtende Schutzgerätezuordnung angepasst und neue Regressionstests für 1.7 ergänzt.

## Ergänzte Regressionstests

- Hostname mit Unterstrich wird verständlich abgelehnt; vorgeschlagene Bindestrich-Variante ist gültig.
- Schnittstellengeschwindigkeiten akzeptieren ausschließlich 100, 1000 und 2500 Mbit/s.
- FRITZ!Box-Adressen werden numerisch sortiert und ungültige/leere Adressen zuletzt angezeigt.
- IP-Abweichungen werden über normalisierte MAC-Adressen erkannt, ohne die dokumentierte IP automatisch zu ändern.
- Ein neuer Stromkreis ohne konkretes Schutzgerät wird abgelehnt; belegte Geräte werden gekennzeichnet und nicht doppelt zugeordnet.
- Asset-Typ-Capability `is_meter` und Bild-Fallback vom individuellen Bild zum Typbild werden geprüft.
- Bestehende Topologietests wurden auf platzierte Schutzgeräte angepasst.

## In dieser Build-Umgebung nicht ausführbar

Der vollständige Backend-Testlauf, `ruff`, `mypy`, `npm test` und der produktive Frontend-Build konnten in der bereitgestellten Arbeitsumgebung nicht abgeschlossen werden, weil die benötigten Python- und Node-Abhängigkeiten nicht lokal vorhanden waren und der konfigurierte Paketindex bei Installationsversuchen nicht erreichbar war. Die statischen Prüfungen ersetzen deshalb nicht den Pflicht-Smoke-Test und den vollständigen CI-Lauf vor produktiver Freigabe.

## Vor produktiver Freigabe

1. `scripts/check.sh` in einer Umgebung mit installierten Entwicklungsabhängigkeiten ausführen.
2. Migration `0046` gegen eine Kopie der produktiven Datenbank testen.
3. Die Smoke-Tests aus `DocOfHome_Runbook_Version_1.7.md` vollständig durchführen.
4. Repair-/Nacharbeitsfälle für Stromkreise ohne Sicherung und alte Phasenwerte prüfen.

## 1.6.3.8 – 2026-07-28

### Changelog

### FI/RCD-Zuordnung aus dem DIN-Asset-Modell

- Phasen-/Kammschienen und N-Schienen bieten jetzt auch FI-Schutzschalter und
  FI/LS-Schalter an, die als normale DIN-Assets in derselben Verteilung platziert sind;
- historische FI/RCD-Datensätze aus `electrical_protective_devices` bleiben
  rückwärtskompatibel auswählbar;
- Schrankkomponenten speichern den neuen Asset-Verweis in `linked_rcd_asset_id` und
  erlauben niemals gleichzeitig einen alten Schutzgeräte- und einen neuen Asset-Verweis;
- der verknüpfte FI/RCD wird in den Schienendetails mit seinem Asset-Namen angezeigt;
- zugeordnete FI/RCD-DIN-Assets können erst nach dem Lösen der Schienenzuordnung aus
  dem Verteiler entfernt werden;
- Migration `0047` ergänzt die neue Referenz ohne bestehende Gruppenzuordnungen zu verändern.

### Release Notes

## FI/RCD-Zuordnung für das aktuelle DIN-Geräte-Modell

Sicherungen, FI/RCD, FI/LS, Relais und weitere Einbaugeräte werden im aktuellen
Verteilerschrank als normale DIN-Assets platziert. Die optionale FI/RCD-Auswahl an
Phasen-/Kammschienen und N-Schienen berücksichtigte bisher jedoch nur das historische
`electrical_protective_devices`-Modell. Dadurch blieb die Auswahlliste leer, obwohl ein
FI-Schutzschalter sichtbar in derselben Verteilung platziert war.

Version 1.6.3.8 erweitert die Zuordnung auf beide Modelle:

- FI-Schutzschalter und FI/LS-Schalter aus den aktiven DIN-Asset-Platzierungen derselben
  Verteilung werden angeboten.
- Historische FI/RCD-Schutzgeräte bleiben weiterhin auswählbar.
- Eine Schiene speichert entweder den historischen Schutzgeräteverweis oder den neuen
  Asset-Verweis, niemals beide gleichzeitig.
- Der ausgewählte FI/RCD wird in den Schienendetails mit seinem Asset-Namen angezeigt.
- Ein als FI/RCD zugeordnetes DIN-Asset kann nicht aus dem Schrank entfernt werden, bevor
  die Schienenzuordnung gelöst wurde.
- Die Klassifikation erfolgt zentral anhand des Asset-Typs, unter anderem für
  `FI-Schutzschalter`, `FI/LS-Schalter`, RCD und RCBO.

## Datenbank

Alembic-Migration `0047` ergänzt `linked_rcd_asset_id` an den Schrankkomponenten. Der
bisherige Verweis `linked_rcd_device_id` bleibt für Altbestände vollständig erhalten.

### Validierung

Stand: 28.07.2026

## Behobener Fehler

Das Auswahlfeld **Zugehöriger FI/RCD (optional)** an Phasen-/Kammschienen und
N-Schienen verwendete nur das historische Schutzgerätemodell. Ein als normales
DIN-Asset platzierter FI-Schutzschalter erschien deshalb nicht in der Liste.

## Umsetzung

- neue Datenbankreferenz `linked_rcd_asset_id` für Schrankkomponenten
- bestehende Referenz `linked_rcd_device_id` bleibt für Altbestände erhalten
- beide Referenzen schließen sich gegenseitig aus
- FI/RCD-DIN-Assets werden zentral anhand ihres Asset-Typs erkannt
- unterstützt werden insbesondere FI-Schutzschalter, FI/LS, RCD, RCBO und
  Fehlerstromschutzschalter
- auswählbar sind nur aktive und in derselben Verteilung platzierte DIN-Assets
- API-Antworten für DIN-Platzierungen enthalten `is_rcd`
- Schienendetails zeigen den Namen des ausgewählten FI/RCD-Assets
- ein verknüpftes FI/RCD-Asset kann nicht aus der Verteilung entfernt werden,
  solange die Zuordnung besteht

## Datenbank

- Alembic-Head: `0047`
- Migration: `0047_link_cabinet_rails_to_din_rcd_assets.py`
- Migrationstest auf SQLite: erfolgreich
- Fremdschlüssel, Index und Ausschluss der doppelten Referenz geprüft

## Ausgeführte Prüfungen

- Versionskonsistenz 1.6.3.8: erfolgreich
- Branding: erfolgreich
- Releasevertrag 1.6.3.8: erfolgreich
- Python-Syntax für App, Migrationen und Tests: erfolgreich
- TypeScript-/Vue-Syntax: 182 Einheiten erfolgreich
- Migrationsprüfungen 0030 bis 0047: erfolgreich
- reine Klassifikationsprüfung für FI/RCD-Asset-Typen: erfolgreich

## Nicht vollständig ausführbar

Der vollständige Pytest-, Ruff-, Mypy-, `vue-tsc`-, Vite- und Docker-Lauf konnte
in dieser Umgebung nicht ausgeführt werden, weil die externen Python-/npm-
Abhängigkeiten beziehungsweise Docker nicht installiert sind. Die dafür
vorgesehenen Tests und Releaseverträge sind im Paket enthalten.

## 1.6.3.7 – 2026-07-28

### Release Notes

Diese Korrektur vereinheitlicht das Daten- und Bedienmodell für Geräte auf der
DIN-Hutschiene.

## Einheitliches Modell

Neue Sicherungen, FI/RCD, FI/LS, Relais, Stromstoßschalter und andere
Hutschienengeräte werden als normale Assets angelegt und anschließend über eine
DIN-Platzierung (`electrical_asset_placements`) in den Verteiler gesetzt. Sie werden nicht mehr über den
separaten Schutzgeräte-Neuanlageweg erzeugt.

Der bisherige `protective_devices`-Pfad bleibt ausschließlich zur
Rückwärtskompatibilität mit bereits vorhandenen Datensätzen bestehen.

## Bedienung

- Die Schrankansicht zeigt nur noch **DIN-Gerät platzieren** als regulären
  Neuanlageweg.
- Der Dialog verwendet weiterhin die am Asset, Produkt oder Asset-Typ
  hinterlegte DIN-Breite.
- Phasen-/Kammschienen verbinden alle vollständig überdeckten DIN-Platzierungen
  automatisch.
- Bestehende Legacy-Schutzgeräte werden weiterhin angezeigt, verschoben,
  archiviert und in der Topologie berücksichtigt.

### Validierung

## Ziel

Prüfung, dass neue Sicherungen und sonstige Hutschienengeräte einheitlich über
DIN-Assets und `electrical_asset_placements` geführt werden, während bestehende
Legacy-Schutzgeräte weiterhin lesbar und verwaltbar bleiben.

## Geprüfte Verträge

- regulärer Neuanlagebutton: `DIN-Gerät platzieren`
- kein sichtbarer Neuanlagebutton für neue `protective_devices`
- Kammschienenservice unterstützt `asset`-Ziele aus DIN-Platzierungen
- Legacy-Ziele vom Typ `protective_device` bleiben rückwärtskompatibel
- Versionskonsistenz 1.6.3.7

## 1.6.3.6 – 2026-07-28

### Changelog

### Asset-Erfassung und DocOfHome-Codes

- der per Migration angelegte Asset-Typ **Smartes Relais / DIN-Schaltaktor**
  besaß keinen Eintrag in `asset_code_counters`; beim Anlegen eines Assets
  schlug deshalb die Reservierung von `SRA-001` mit HTTP 500 fehl;
- Migration `0046_repair_asset_code_counters` ergänzt fehlende Zähler für alle
  Asset-Typen und hebt veraltete Zähler mindestens auf die höchste vorhandene
  DocOfHome-Nummer plus eins an;
- die Codevergabe rekonstruiert einen fehlenden Zähler zusätzlich zur Laufzeit,
  damit auch zukünftige inkonsistente Stammdaten nicht mehr zu HTTP 500 führen.

### Release Notes

Diese Korrektur behebt einen HTTP-500-Fehler beim Anlegen von Assets für
Stammdaten, die per Migration angelegt wurden.

## Behoben

Der Asset-Typ **Smartes Relais / DIN-Schaltaktor** wurde zusammen mit dem
Produkt **Shelly Pro 1** bereitgestellt. Dabei fehlte jedoch der zugehörige
Nummernkreis `SRA` in `asset_code_counters`. Beim Anlegen des ersten Geräts
konnte deshalb kein DocOfHome-Code wie `SRA-001` reserviert werden.

## Datenreparatur

Migration `0046_repair_asset_code_counters`:

- ergänzt fehlende Nummernkreise für sämtliche Asset-Typen;
- ermittelt die höchste bereits verwendete Nummer aus den vorhandenen
  `jarvis_code`-Werten;
- setzt einen vorhandenen, aber zu niedrigen Zähler auf die nächste freie Nummer;
- verändert keine bestehenden Asset-Codes.

Die Laufzeitlogik besitzt zusätzlich einen selbstheilenden Fallback: Fehlt trotz
Migration ein Zähler, wird er beim nächsten Anlegen eines Assets aus den bereits
vergebenen Codes rekonstruiert.

### Validierung

Stand: 28.07.2026

## Gemeldeter Fehler

Beim Anlegen eines Assets mit dem Asset-Typ **Smartes Relais / DIN-Schaltaktor**
und dem Produkt **Shelly Pro 1** antwortete die API mit HTTP 500.

## Ursache

Migration `0038_release_1_6_1_corrections` legte den Asset-Typ mit dem
Codepräfix `SRA` und das Produkt an, erzeugte jedoch keinen zugehörigen Eintrag
in `asset_code_counters`. Die Codevergabe verwendete bei der ersten Erfassung
ein `UPDATE ... RETURNING` und erwartete zwingend einen vorhandenen Zähler.
Ohne Datensatz endete `scalar_one()` mit einer unbehandelten Ausnahme.

## Korrekturen

- Migration `0046_repair_asset_code_counters` ergänzt fehlende Zähler für alle
  Asset-Typen.
- Vorhandene, aber zu niedrige Zähler werden auf die höchste vergebene Nummer
  plus eins angehoben.
- Bestehende `jarvis_code`-Werte werden nicht verändert.
- Die Laufzeit-Codevergabe verwendet `scalar_one_or_none()` und rekonstruiert
  einen fehlenden Zähler selbstheilend aus vorhandenen Codes.
- Ein Backend-Regressionstest bildet einen fehlenden `SRA`-Zähler mit bereits
  vorhandenem `SRA-007` ab und erwartet anschließend `SRA-008` und `SRA-009`.

## Ausgeführte Prüfungen

- Versionskonsistenz `1.6.3.6`: bestanden
- Releasevertrag `1.6.3.6`: bestanden
- Branding und gesammelte Korrekturverträge: bestanden
- Elektro- und Kammschienenverträge: bestanden
- Python-Syntax für Backend, Migrationen, Tests und Prüfscripte: bestanden
- Syntax von 181 TypeScript-/Vue-Skripteinheiten: bestanden
- alle vorhandenen Migrationsprüfungen `0030` bis `0046`: bestanden
- Migration `0046`: fehlender Zähler, veralteter Zähler und Idempotenz geprüft

## Nicht in dieser Umgebung ausführbar

- vollständige Pytest-Suite, da `sqlmodel` nicht installiert ist
- Ruff und Mypy mit den Projektabhängigkeiten
- `npm test` und `npm run build`, da `node_modules` nicht vorhanden ist
- Docker-Build, da Docker in der Build-Umgebung nicht verfügbar ist

Diese Einschränkungen betreffen nicht die erfolgreich ausgeführte isolierte
SQLite-Migrationsprüfung und die statischen/Syntaxprüfungen der Korrektur.

## 1.6.3.5 – 2026-07-28

### Changelog

### Kammschienen und DIN-Kontakte

- automatische Schienenverbindungen gelten nun für jedes vollständig überdeckte
  DIN-Gerät, unabhängig davon, ob es als Schutzgerät oder allgemeines DIN-Asset
  modelliert ist;
- allgemeine DIN-Assets werden als Topologie-Ziel `asset` angebunden und erhalten
  die Phase aus ihrer TE-Position;
- vierpolige FI/RCD- und FI/LS-Geräte verwenden auf einer dreiphasigen
  Kammschiene nur die ersten drei Außenleiterkontakte; der vierte Pol bleibt für
  N frei; diese Lage wird sowohl beim Platzieren des Geräts als auch beim späteren
  Anlegen der Schiene validiert;
- zusätzliche manuelle Einspeisungen zu automatisch kontaktierten DIN-Geräten
  werden verhindert;
- teilweise Überdeckungen werden sowohl beim Anlegen der Schiene als auch beim
  Verschieben eines DIN-Geräts verhindert;
- automatische Verbindungen werden beim Platzieren, Verschieben, Entfernen,
  Topologieaufruf und Schienenupdate idempotent synchronisiert;
- Migration `0045_phase_rail_all_din_contacts` ergänzt und repariert Kontakte im
  vorhandenen Datenbestand;
- Release- und Changeloganzeige unterstützen vierteilige Korrekturversionen wie
  `1.6.3.5`.

### Release Notes

Diese Korrektur richtet die Kammschienenlogik am tatsächlichen Aufbau einer
DIN-Reihe aus. Eine Phasen-/Kammschiene kontaktiert nicht nur explizit als
Schutzgerät modellierte Einträge, sondern jedes vollständig überdeckte
DIN-Hutschienengerät.

## Behoben

- Als allgemeine DIN-Assets platzierte Sicherungen und Stromstoßschalter wurden
  bisher in der Schrankansicht angezeigt, aber von der automatischen
  Verkabelung nicht gefunden.
- Die Erfolgsmeldung konnte deshalb trotz sichtbarer Geräte `0` Kontakte melden.
- Teilweise unter einer Kammschiene liegende allgemeine DIN-Geräte waren möglich,
  obwohl deren Kontaktlage physisch nicht eindeutig ist.

## Neue Kontaktlogik

- Quelle jeder automatischen Verbindung ist die Phasen-/Kammschiene.
- Ziel ist entweder ein Schutzgerät oder das Asset einer allgemeinen
  DIN-Platzierung.
- Die Kontaktphase folgt Startphase und TE-Position.
- Mehrteilige allgemeine DIN-Geräte erhalten alle Phasen ihrer belegten Kontakte.
- Bei einem vierpoligen FI/RCD oder FI/LS werden ausschließlich L1, L2 und L3
  über die Schiene geführt; Pol 4 bleibt für N frei. Die zulässige Lage wird beim
  Platzieren des Geräts und beim späteren Anlegen der Schiene geprüft.
- Die Kontakte sind abgeleitet und können nicht manuell bearbeitet oder gelöscht
  werden. Zusätzliche manuelle Einspeisungen zu einem automatisch kontaktierten
  DIN-Gerät sind ebenfalls gesperrt.

## Datenbank

Migration `0045` ergänzt fehlende Schienenkontakte für vorhandene
DIN-Asset-Platzierungen und aktualisiert bestehende Kontakte idempotent.

### Validierung

Stand: 28.07.2026

## Anlass und bestätigte Ursache

Die reale Laufzeitanalyse zeigte, dass die im Verteilerschrank sichtbaren Geräte
nicht ausschließlich als `electrical_protective_devices`, sondern teilweise als
allgemeine `electrical_asset_placements` gespeichert sind. Die bisherige
Kammschienen-Synchronisation suchte überwiegend Schutzgeräte und konnte deshalb
trotz sichtbarer Sicherungen und Stromstoßschalter null Kontakte erzeugen.

## Umsetzung

- Jede vollständig von einer Phasen-/Kammschiene überdeckte DIN-Platzierung wird
  als physischer Kontakt behandelt.
- Schutzgeräte werden über den Endpunkt `protective_device`, allgemeine
  DIN-Platzierungen über den Endpunkt `asset` angebunden.
- Quelle der abgeleiteten Verbindung ist die Kammschiene; Ziel ist das jeweilige
  DIN-Gerät.
- Kontaktphasen folgen Startphase, TE-Position und belegter Breite.
- Ein vierpoliger FI/RCD oder FI/LS erhält L1, L2 und L3; der vierte Pol bleibt
  für N frei. Die zulässige Lage wird sowohl beim Platzieren des Geräts als auch
  beim späteren Anlegen der Schiene validiert.
- Zusätzliche manuelle Einspeisungen zu automatisch kontaktierten DIN-Geräten
  werden verhindert.
- Nachgelagerte Verbindungen allgemeiner DIN-Geräte übernehmen ebenfalls die
  wirksamen Schienenphasen.
- Anzeige, Kollisionsprüfung, Endpunktprojektion und automatische Verkabelung
  verwenden dieselbe wirksame DIN-Breite einschließlich Vererbung von Asset,
  Produkt oder Asset-Typ.
- Platzieren, Verschieben und Entfernen synchronisiert die Kontakte idempotent.
- Migration `0045` ergänzt die Kontakte für vorhandene DIN-Asset-Platzierungen
  und repariert bestehende Schienenbeziehungen.

## Erfolgreich ausgeführte Prüfungen

- Versions- und Brandingvertrag für `1.6.3.5`
- Releasevertrag und Elektro-Integritätsverträge
- Laufzeit-Quellvertrag für Schutzgeräte und allgemeine DIN-Assets
- Phasenmuster einschließlich vierpoligem FI-Sonderfall
- geerbte DIN-Breiten in Synchronisation und Platzierungsprüfung
- Syntax von 181 TypeScript-/Vue-Skripteinheiten
- Syntax von 280 Python-Dateien
- Migrationsprüfungen `0030` bis `0037` und `0039` bis `0045`
- Migration `0045` mit generischen DIN-Assets, L1/L2/L3-Folge,
  vierpoligem FI ohne N-Kontakt und wiederholtem idempotentem Upgrade
- ZIP-Kompressions-, Extraktions-, Manifest- und SHA-256-Prüfung

## Nicht vollständig ausführbare Prüfungen

- Die vollständige Pytest-Suite konnte in dieser Umgebung nicht ausgeführt
  werden, weil `sqlmodel` nicht installiert und nicht aus einem lokalen Cache
  verfügbar ist.
- `npm ci --offline` konnte nicht abgeschlossen werden, weil mindestens das
  Paket `why-is-node-running` nicht im npm-Cache vorhanden ist. Daher waren
  `vue-tsc`, Vitest und der vollständige Vite-Produktionsbuild hier nicht
  ausführbar.
- Docker ist in dieser Umgebung nicht installiert; ein Containerbuild konnte
  daher nicht lokal wiederholt werden.
- `ruff` ist nicht installiert. Stattdessen wurden Python-Syntax, Zeilenlängen
  und geänderte Importverwendungen separat geprüft.

## 1.6.3.4 – 2026-07-28

### Release Notes

## Kammschienen-Automatik: geerbte DIN-Breiten

Die Laufzeitdaten des Anwenders zeigten, dass der explizite Synchronisations-Endpunkt
erfolgreich aufgerufen wurde, aber weiterhin null Schutzgeräte erkannte. Der Grund war
eine unterschiedliche Breitenlogik:

- Die Verteilerschrankansicht verwendet die wirksame DIN-Breite vom Asset, Produkt oder
  Asset-Typ, wenn `electrical_protective_devices.module_width` bei älteren Datensätzen leer ist.
- Die automatische Kammschienen-Verkabelung prüfte bislang nur die lokale Spalte des
  Schutzgeräts und verwarf solche sichtbar platzierten Geräte.

Die Implementierung nutzt dafür `effective_asset_module_width`.

1.6.3.4 verwendet für Erkennung, vollständige TE-Überdeckung, Phasenberechnung und
Verifikation exakt dieselbe Vererbungskette wie die Schrankansicht.

### Ergebnis

Für vollständig überdeckte Schutzgeräte wird automatisch erzeugt:

- Quelle: Phasen-/Kammschiene
- Ziel: Schutzgerät
- Verbindungsart: Sammelschiene/Phasenschiene
- Außenleiter: gemäß Startphase und TE-Position

Allgemeine DIN-Assets bleiben weiterhin unverbunden. Im Serverlog wird jeder explizite
Synchronisationslauf mit Anzahl übermittelter, erkannter und abgelehnter Geräte protokolliert.

Alembic bleibt auf Revision `0044`; die Laufzeitkorrektur repariert Bestandsdaten beim
Speichern der Schiene oder beim Öffnen der Topologie.

### Validierung

## Behobener Laufzeitfehler

Die Kammschienen-Synchronisation verwendet nun `effective_asset_module_width` als Fallback,
wenn die historische Schutzgeräte-Spalte `module_width` leer ist. Das entspricht exakt der
Breitenanzeige der Verteilerschrankansicht.

## Abgesicherte Verträge

- Kandidatenermittlung akzeptiert geerbte DIN-Breiten
- TE-Überdeckung verwendet die wirksame statt nur der lokalen Breite
- Phasenberechnung verwendet dieselbe wirksame Breite
- serverseitige Fallback-Suche verwirft geerbte Breiten nicht mehr
- Regressionstest simuliert `electrical_protective_devices.module_width = NULL` bei
  `asset_types.module_width = 1`
- Synchronisationslauf schreibt Diagnosewerte in das Serverlog

## Ausgeführte Prüfungen

- Python-Syntaxprüfung
- Versions- und Releaseverträge
- dependency-freie Elektro- und Phasenschienenverträge
- TypeScript-/Vue-Syntaxprüfung
- ZIP- und Manifestprüfung

Die vollständige Pytest-Suite konnte in der Buildumgebung nicht ausgeführt werden, da das
Python-Paket `sqlmodel` nicht installiert und nicht aus dem Paketnetz abrufbar ist. Der
konkrete Regressionstest ist im Release enthalten und kann im Docker-Build ausgeführt werden.

## 1.6.3.3 – 2026-07-28

### Release Notes

## Behoben

- Phasen-/Kammschienen verwenden nach dem Speichern einen eigenen Synchronisations-Endpunkt.
- Die Verteilerschrankansicht übermittelt die tatsächlich sichtbaren Schutzgeräte-IDs ohne fragile Frontend-Filter auf optionale Bestandsfelder.
- Das Backend lädt jedes gemeldete Schutzgerät direkt aus Schutzgeräte-, Komponenten- und Asset-Tabelle und validiert Verteilung, Bereich, Reihe und vollständige TE-Überdeckung.
- Für jedes passende Schutzgerät wird verbindlich eine schreibgeschützte Verbindung **Phasen-/Kammschiene → Schutzgerät** mit automatisch berechneter Phase erzeugt.
- Kann kein sichtbares Schutzgerät zugeordnet werden, erscheint ein konkreter Diagnosefehler statt einer irreführenden Erfolgsmeldung mit `0 Schutzgerät(en)`.
- Scheitert die Kontaktsynchronisation nach dem erstmaligen Anlegen, bleibt der Dialog im Bearbeitungsmodus und erzeugt beim erneuten Speichern keine doppelte Schiene.

## Datenbank

Keine neue Migration erforderlich. Alembic-Head bleibt `0044`.

### Validierung

Stand: 28.07.2026

## Anlass

In 1.6.3.2 wurde beim Speichern einer sichtbaren Phasen-/Kammschiene weiterhin
`automatisch mit 0 Schutzgerät(en) verbunden` gemeldet. Damit war belegt, dass
der implizite Synchronisationslauf keine passenden Geräte erkannte und trotzdem
eine irreführende Erfolgsmeldung zurückgab.

## Korrektur

- Nach dem Speichern einer Phasen-/Kammschiene ruft das Frontend einen eigenen
  Synchronisations-Endpunkt auf.
- Die Verteilerschrankansicht übermittelt alle aktuell sichtbaren Schutzgeräte-IDs
  der Verteilung. Fragile Frontend-Filter auf `deleted_at`, Platzierungsfelder oder
  optionale Bestandsattribute wurden entfernt.
- Das Backend lädt jedes gemeldete Schutzgerät direkt aus
  `electrical_protective_devices`, `electrical_components` und `assets`.
- Serverseitig werden Verteilung, Bereich, Reihe, vollständige TE-Überdeckung,
  Lebenszyklus und berechenbare Phase geprüft.
- Für jedes passende Gerät wird eine aktive, schreibgeschützte Verbindung
  `Phasen-/Kammschiene -> Schutzgerät` erzeugt oder reaktiviert.
- Alte konkurrierende Einspeisungen werden vor Aktivierung des automatischen
  Kontakts archiviert; Messpunktbezüge werden auf den neuen Kontakt umgehängt.
- Werden sichtbare Geräte gemeldet, aber kein Kontakt erzeugt, antwortet der
  Endpunkt mit einem konkreten Diagnosefehler je Gerät. Eine erfolgreiche
  Rückgabe mit `0 Schutzgerät(en)` ist in diesem Fall ausgeschlossen.
- Scheitert die Synchronisation nach dem erstmaligen Anlegen, bleibt der Dialog
  im Bearbeitungsmodus, damit beim erneuten Speichern keine doppelte Schiene
  entsteht.

## Ausgeführte Prüfungen

Erfolgreich:

- Versionskonsistenz 1.6.3.4
- Branding- und Releaseverträge
- Elektro-Integritätsverträge
- Laufzeitvertrag der Kammschienen-Synchronisation
- dependency-freier SQLite-Test für L1/L2/L3 und den Austausch einer bestehenden
  Einspeisung unter historischem Eindeutigkeitsindex
- Python-Syntax aller Backend-, Migrations-, Test- und Prüfscripte
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten
- Migrationsprüfungen 0030 bis 0044
- Releaseprüfung aus einem frisch entpackten ZIP
- ZIP-Kompressions- und Manifestprüfung

Nicht vollständig ausführbar:

- `npm ci` / `npm run build`: Der konfigurierte npm-Paketserver lieferte beim
  Abruf von `why-is-node-running-2.3.0.tgz` HTTP 503.
- vollständige Pytest-/Alembic-Anwendungssuite: Die benötigten externen
  Python-Abhängigkeiten konnten in dieser Umgebung nicht aus dem Paketserver
  installiert werden.

## Datenbank

Keine neue Migration erforderlich. Alembic-Head bleibt `0044`.

## 1.6.3.2 – 2026-07-28

### Release Notes

Stand: 28. Juli 2026

## Anlass

Beim Speichern einer Phasen-/Kammschiene meldete die Anwendung weiterhin
„automatisch mit 0 Schutzgeräten verbunden“, obwohl in derselben sichtbaren
Reihe vollständig überdeckte Sicherungen vorhanden waren.

## Korrektur

Die Verteilerschrankansicht übermittelt beim Speichern die IDs der sichtbar und
vollständig überdeckten Schutzgeräte. Das Backend vertraut diesen IDs nicht
blind, sondern prüft jedes Gerät erneut auf aktive Existenz, Verteilung, Bereich,
Reihe, TE-Spanne und berechenbare Phase. Anschließend werden die abgeleiteten
Kontakte zwingend erzeugt.

Parallel bleibt eine unabhängige serverseitige Suche aktiv. Sie verbindet den
kanonischen Repositorypfad mit einem direkten, lebenszyklusgeprüften Tabellen-
Fallback für ältere aktualisierte SQLite-Datenbanken.

Für Bestände mit einer alten Eindeutigkeitsregel wird der neue Kontakt zunächst
inaktiv angelegt. Danach werden konkurrierende manuelle Einspeisungen und
Messbezüge umgehängt; erst anschließend wird der Kammschienenkontakt aktiviert.

## Ergebnis

- Quelle: Phasen-/Kammschiene;
- Ziel: jedes vollständig überdeckte aktive Schutzgerät;
- Phase: aus Startphase und TE-Position;
- allgemeine DIN-Assets bleiben unverbunden;
- ein erwarteter Kontakt darf nicht still fehlen.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0044`.

### Validierung

Stand: 28. Juli 2026

## Anlass

In DocOfHome 1.6.3.1 konnte das Speichern einer Phasen-/Kammschiene weiterhin
„automatisch mit 0 Schutzgerät(en) verbunden“ melden, obwohl in der sichtbaren
Reihe vollständig überdeckte Sicherungen vorhanden waren.

## Technische Ursache

Die serverseitige Geräteermittlung konnte auf langfristig migrierten SQLite-
Datenbanken von der im Frontend sichtbaren Schutzgeräteliste abweichen. Außerdem
kann in älteren Datenbanken noch die historische Regel existieren, nach der ein
Ziel nur eine aktive Einspeisung besitzen darf. Dann muss eine vorhandene
manuelle Einspeisung deaktiviert werden, bevor der neue Kammschienenkontakt
aktiviert wird.

## Korrekturen

- Die Schrankansicht übermittelt beim Speichern alle aktuell sichtbaren
  Schutzgeräte-IDs der Verteilung.
- Das Backend prüft jede ID erneut auf aktive Existenz, Verteilung, Bereich,
  Reihe, vollständige TE-Überdeckung und berechenbare Phase.
- Die ID-Auflösung verwendet zuerst das kanonische Repository und fällt bei
  unvollständigen Projektionen direkt auf Basistabellen zurück.
- Die unabhängige serverseitige Verteilungssuche verbindet Repository und
  direkten lebenszyklusgeprüften Tabellen-Fallback.
- Neue automatische Kontakte werden zunächst inaktiv gespeichert.
- Vorhandene manuelle Einspeisungen und Messpunkte werden auf den neuen Kontakt
  umgehängt beziehungsweise archiviert.
- Erst danach wird der Kammschienenkontakt aktiv geschaltet.
- Bei vom Frontend gemeldeten Geräten ohne einen einzigen gültigen Kontakt wird
  der Speichervorgang mit einer verständlichen Fehlermeldung abgebrochen.
- Allgemeine DIN-Assets bleiben von der automatischen Verkabelung ausgenommen.

## Ausgeführte Prüfungen

- Versionskonsistenz 1.6.3.2
- Branding- und gesammelte Releaseverträge
- Elektro-Integritätsverträge 1.6.3
- expliziter Laufzeitvertrag für Kammschienen-Synchronisation
- echter SQLite-Laufzeittest mit:
  - L1/L2/L3-Ermittlung für TE 1/2/3;
  - historischer partieller Eindeutigkeitsregel für aktive Ziele;
  - inaktivem Vorabkontakt;
  - Umhängen eines Smart-Meter-Messpunkts;
  - Archivierung der alten Einspeisung;
  - anschließender Aktivierung des neuen Kontakts
- Python-Syntax aller Backend-, Migrations- und Testdateien
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten
- Migrationstests 0030 bis 0044
- ZIP-Kompressions-, Extraktions- und Manifestprüfung

## Nicht vollständig ausführbar

Die vollständige Pytest-Suite konnte in dieser Build-Umgebung nicht ausgeführt
werden, weil `sqlmodel` lokal nicht verfügbar war. `npm ci` konnte nicht komplett
aus dem lokalen Cache hergestellt werden, da das Paket `why-is-node-running`
fehlte. Der produktive Vue-/Vite-Build wurde daher hier nicht erneut vollständig
ausgeführt. Die geänderten Python-Dateien, Pydantic-Payloads und alle
TypeScript-/Vue-Skripteinheiten wurden syntaktisch geprüft.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0044`.

## 1.6.3.1 – 2026-07-28

### Release Notes

Stand: 28. Juli 2026

## Anlass

In realen, über mehrere Versionen aktualisierten Datenbanken konnten Schutzgeräte in der
Schrankansicht sichtbar sein, während die separate Abfrage der automatischen
Kammschienen-Verkabelung dieselben Geräte nicht fand. Das Speichern meldete deshalb
„automatisch mit 0 Schutzgeräten verbunden“.

## Korrektur

Die automatische Verkabelung verwendet nun exakt denselben kanonischen
Schutzgeräte-Repositorypfad wie die Schrank- und Verteilungsansicht. Damit existiert nur
noch eine Definition für ein aktives, sichtbares Schutzgerät.

Beim Anlegen, Ändern oder Öffnen der Topologie gilt:

- Quelle: Phasen-/Kammschiene;
- Ziel: jedes vollständig überdeckte aktive Schutzgerät;
- Phase: automatisch aus Startphase und TE-Position;
- allgemeine DIN-Assets bleiben unverbunden;
- bestehende archivierte Automatikkontakte werden reaktiviert;
- konkurrierende manuelle Eingänge des Schutzgeräts werden ersetzt.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0044`. Der Laufzeitabgleich repariert bereits
vorhandene Schienen beim Speichern oder beim Öffnen der Topologie.

## Update

Das Image muss ohne Cache neu gebaut und der Browser anschließend hart aktualisiert werden.

### Validierung

Stand: 28. Juli 2026

## Ausgangslage

Beim Speichern einer Phasen-/Kammschiene meldete DocOfHome trotz sichtbar und vollständig
überdeckter Sicherungen „automatisch mit 0 Schutzgeräten verbunden“. Die Schrankansicht und
die Automatiksynchronisation ermittelten aktive Schutzgeräte über zwei unterschiedliche
Datenpfade. Auf über mehrere Releases aktualisierten SQLite-Datenbanken konnten diese
Ergebnisse auseinanderlaufen.

## Korrektur

`PhaseRailConnectionService._devices_for_distribution()` verwendet jetzt
`ElectricalProtectiveDeviceRepository.for_distribution(..., include_deleted=False)`.
Dies ist derselbe kanonische Repositorypfad, über den die sichtbaren Schutzgeräte der
Verteilung bereitgestellt werden.

Damit gilt:

- jedes aktive Schutzgerät, das in der Verteilungsansicht sichtbar ist, steht auch der
  automatischen Kammschienen-Verkabelung zur Verfügung;
- vollständig überdeckte Schutzgeräte erhalten Quelle = Phasen-/Kammschiene und
  Ziel = Schutzgerät;
- allgemeine DIN-Assets bleiben von der automatischen Verkabelung ausgeschlossen;
- die vorhandene Verifikation bricht den Speichervorgang ab, falls erwartete Kontakte
  trotz erkannter Geräte fehlen oder eine falsche Phase besitzen;
- bestehende Schienen werden beim Speichern beziehungsweise beim Öffnen der Topologie
  erneut abgeglichen.

## Version und Datenbank

- Release: `1.6.3.1`
- Basis: `1.6.3`
- Alembic-Head: `0044`
- keine neue Migration erforderlich

## Erfolgreich ausgeführte Prüfungen

- zentrale Versionskonsistenz in `VERSION`, Backend, Frontend, Lockdatei und
  `SOURCE_INFO.json`;
- Branding- und gesammelte Korrekturverträge;
- Ableseerinnerungs-Verträge;
- Releasevertrag 1.6.3.1;
- Elektro-Integritätsverträge 1.6.3;
- neuer Laufzeitvertrag für den kanonischen Schutzgeräte-Repositorypfad;
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten;
- Python-Syntaxprüfung von Backend, Migrationen und Tests;
- dependency-freie Migrationsprüfungen 0030 bis 0044;
- ZIP-Kompressionsprüfung, erneute Extraktion und Manifestprüfung.

## Nicht ausführbare vollständige Gates

In der verfügbaren Umgebung fehlen `ruff`, `mypy`, `sqlmodel`/Pytest-Abhängigkeiten und
die installierten Frontend-Abhängigkeiten. Daher konnten die vollständigen Ruff-, mypy-,
Pytest-, Vitest-, vue-tsc-/Vite- und Docker-Läufe nicht erneut ausgeführt werden. Die
zugehörigen Quellen und Tests sind im Paket enthalten.

## 1.6.3 – 2026-07-27

### Changelog

### Build-Korrektur

- `phaseRailAutoWiring.test.ts` verwendet jetzt wie die übrigen Frontend-Quellvertragstests
  einen Vite-`?raw`-Import. Dadurch benötigt `vue-tsc` im Browserprojekt weder `node:fs`
  noch separate Node-Typdefinitionen.
- Der Releasevertrag prüft ausdrücklich, dass dieser Test keine Node-Builtin-Imports mehr
  in den produktiven TypeScript-Build einbringt.

### Elektro-Integrität

- zentrale und einheitliche Phasenberechnung für Phasenschiene, Schutzgerät,
  Stromkreis, Topologie und Smart-Meter-Messpunkt;
- automatische, schreibgeschützte Verbindungen von Phasen-/Kammschienen zu
  vollständig überdeckten Schutzgeräten;
- klare Trennung von automatisch verwalteter Phasenschiene und manuell
  dokumentierter allgemeiner Sammelschiene;
- legitime vorgelagerte FI/RCD-Einspeisungen einer Phasenschiene bleiben bei
  der Automatiksynchronisierung erhalten;
- Teilüberdeckungen, konkurrierende Phasenschienen und unzulässige DIN-Asset-
  Überdeckungen werden zentral abgewiesen;
- Stromkreisphasen werden aus Schutzgerät oder dokumentierter Einspeisung
  übernommen und an Verbraucher weitergegeben;
- Smart-Meter-Messphasen werden gegen die wirksamen Leiter der Verbindung
  validiert und bei eindeutigen einphasigen Verbindungen automatisch gesetzt;
- FI-, N- und PE-Beziehungen einschließlich Typwechsel, Archivierung und
  RCBO-Sonderfall konsistent validiert;
- Schutzgeräte, Stromkreise, Schrankkomponenten und Assets können bei aktiven
  manuellen Elektro-Beziehungen nicht unbemerkt archiviert, ersetzt oder
  verschoben werden;
- Migration `0043_release_1_6_3_electrical_integrity` repariert eindeutige
  Bestandsbeziehungen und ergänzt Schienen-Constraints.

### Release Notes

Veröffentlicht: 27. Juli 2026

DocOfHome 1.6.3 baut auf 1.6.2 auf und überprüft das Elektro-Modul als
zusammenhängendes System. Dabei wurden nicht nur einzelne Dialogfehler, sondern
die Beziehungen zwischen Platzierung, automatischer Verkabelung, Topologie,
Stromkreisen, Messpunkten und Archivierung vereinheitlicht.

## Wichtigste Korrekturen

### Phasen-/Kammschienen

- Eine Phasen-/Kammschiene erzeugt automatisch genau eine schreibgeschützte
  Verbindung zu jedem vollständig überdeckten Schutzgerät.
- Neue, verschobene oder technisch geänderte Schutzgeräte synchronisieren ihre
  Schienenverbindung und Außenleiterphase automatisch.
- Teilüberdeckungen, mehrere gleichzeitig phasenbestimmende Schienen und
  Phasenschienen über beliebigen DIN-Assets werden abgewiesen.
- Die optionale FI/RCD-Zuordnung ist keine Voraussetzung für eine Kammschiene.
- Eine legitime Einspeisung **FI/RCD → Phasenschiene** bleibt erhalten und wird
  nicht mit den automatisch verwalteten Ausgängen verwechselt.
- Manuelle Verbindungen allgemeiner Sammelschienen werden nicht mehr als
  Kammschienen-Automatik archiviert oder umgeschrieben.

### Wirksame Phasen und Topologie

- Die Außenleiterphase wird zentral aus Startphase, TE-Position, Gerätetyp und
  Polzahl berechnet.
- Automatische Kammschienen-Verbindungen können weder bearbeitet noch gelöscht
  werden; Änderungen erfolgen über Schiene oder Geräteplatzierung.
- Nachgelagerte Verbindungen eines phasenbestimmten Schutzgeräts werden auf die
  wirksame Außenleiterphase synchronisiert; N und PE bleiben erhalten.
- Stromkreise übernehmen ihre wirksame Phase aus Schutzgerät oder dokumentierter
  Einspeisung und geben sie verbindlich an Verbraucher weiter.
- Topologie und Bearbeitungsdialog verwenden die serverseitig berechneten
  gesperrten Phasen statt historischer manueller Werte.
- Fehlende oder unvollständige Einspeisungen von Schrankkomponenten werden als
  nachvollziehbare Warnung angezeigt.

### FI-, N- und PE-Beziehungen

- FI/RCD-Verknüpfungen sind nur an Phasenschienen und N-Schienen zulässig.
- Eine N-Schiene kann nicht archiviert oder in einen anderen Typ umgewandelt
  werden, solange Schutzgeräte sie verwenden.
- Widersprüche zwischen manueller FI-Zuordnung, Kammschiene und N-Schiene werden
  validiert.
- FI/LS-Geräte (RCBO) erzeugen keine falsche Warnung wegen einer fehlenden
  separaten N-Schiene.

### Smart Meter und Messpunkte

- Ein Messpunkt kann nur L1/L2/L3/N auswählen, wenn dieser Leiter auf der
  wirksamen Verbindung vorhanden ist.
- Bei genau einer wirksamen Außenleiterphase wird sie automatisch übernommen.
- Beim Reparieren oder Ersetzen automatischer Schienenverbindungen bleiben
  Messpunkte erhalten und werden auf die autoritative Verbindung umgehängt.

### Lebenszyklus und Archivierung

- Schutzgeräte mit manuellen aktiven Verbindungen können nicht archiviert
  werden; nur die automatisch abgeleitete Kammschienen-Verbindung wird intern
  verwaltet.
- Stromkreise mit aktiven Topologieverbindungen können nicht archiviert werden.
- Allgemeine Assets können nicht archiviert, ersetzt oder an einen anderen Ort
  verschoben werden, solange aktive elektrische Verbindungen auf sie zeigen.
- Layoutwechsel und Komponententypwechsel prüfen nun alle abhängigen
  Platzierungen und Beziehungen.

## Migration 0043

Migration `0043_release_1_6_3_electrical_integrity`:

- normalisiert Leiter und FI-Verweise an Phasen-, N- und PE-Schienen;
- repariert eindeutige automatische Phasenschienen-Verbindungen;
- bewahrt legitime vorgelagerte FI/RCD-Einspeisungen;
- korrigiert nachgelagerte Außenleiter und Smart-Meter-Messphasen;
- ergänzt Datenbank-Constraints für die Schienentypen.

## Update von 1.6.2

1. Persistent gespeicherten `data`-Ordner vollständig sichern.
2. Container stoppen: `docker compose down`.
3. DocOfHome 1.6.3 in einen neuen sauberen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. Neu bauen: `docker compose build --no-cache`.
6. Starten: `docker compose up -d`.
7. Logs prüfen: `docker compose logs -f jarvis`.

Im Log muss das Upgrade `0042 -> 0043` erfolgreich durchlaufen. Anschließend
Browsercache vollständig aktualisieren.

## Hinweis

DocOfHome dokumentiert die bestehende Elektroinstallation. Es ersetzt keine
Planung, Prüfung oder Freigabe durch eine Elektrofachkraft.
## Nachträgliche Build-Korrektur

Der Quellvertragstest für die automatische Phasenschienen-Verkabelung liest die Vue-Datei
nun über Vites `?raw`-Import. Der vorherige Import von `node:fs` war mit dem bewusst
browserorientierten `tsconfig.json` nicht vereinbar und ließ `vue-tsc --noEmit` abbrechen.
Die Laufzeitlogik und die Datenmigration 0043 bleiben unverändert.

## Nachträgliche Korrektur der Schrankansicht und Selbstheilung

- Bereits angelegte Schutzgeräte können innerhalb des Bereichs einer
  Phasen-/Kammschiene wieder per Drag-and-drop verschoben werden. Eine
  Teilüberdeckung bleibt weiterhin unzulässig.
- Allgemeine DIN-Assets wie ein Stromstoßschalter werden klar von Schutzgeräten
  unterschieden. Sie dürfen nicht unter eine Kammschiene gezogen werden und
  erhalten nun eine eindeutige Fehlermeldung.
- Fehlende automatische Verbindungen **Phasenschiene → Schutzgerät** werden beim
  Öffnen der Topologie beziehungsweise der Verbindungsliste selbstheilend
  rekonstruiert. Die Synchronisierung wird vor der Auswertung sicher geflusht
  und ist im stabilen Zustand idempotent.
- In der Detailseitenleiste stehen für Schutzgeräte und Schrankkomponenten
  Archivieren-Schaltflächen zur Verfügung.
- Beim Archivieren einer Phasen-/Kammschiene bleiben die Sicherungen platziert;
  die Einspeisung der Schiene und ihre automatisch abgeleiteten Kontakte werden
  gemeinsam historisch archiviert.

## Nachträgliche Korrektur: gemischte DIN-Reihen und Dialogfehler

- Phasen-/Kammschienen dürfen nun über allgemeinen DIN-Geräten wie Stromstoßschaltern dargestellt werden.
- Solche DIN-Geräte werden ausdrücklich nicht automatisch mit der Kammschiene verkabelt.
- Automatische Schienenkontakte entstehen weiterhin ausschließlich für vollständig überdeckte Schutzgeräte.
- Allgemeine DIN-Geräte können auch nachträglich innerhalb des dargestellten Schienenbereichs platziert oder verschoben werden.
- Die Fehlermeldung des Schrankkomponenten-Dialogs liegt nun im scrollbaren Dialoginhalt und wird nicht mehr hinter den Aktionsschaltflächen abgeschnitten.

### Validierung

Stand: 27. Juli 2026  
Ausgangsbasis: DocOfHome 1.6.2  
Schwerpunkt: vollständige Beziehungs- und Integritätsprüfung des Elektro-Moduls

## Prüfumfang

Die Prüfung wurde nicht auf einzelne Dialoge begrenzt. Untersucht wurden die
zusammenhängenden Abläufe und Beziehungen zwischen:

- Verteilungen, Feldern, Gerätebereichen und DIN-Platzierungen;
- Schutzgeräten, Phasen-/Kammschienen und allgemeinen Sammelschienen;
- FI/RCD-, FI/LS-, N- und PE-Beziehungen;
- manuellen und automatisch verwalteten Versorgungsverbindungen;
- wirksamen Phasen in Topologie, Stromkreisen und Verbrauchern;
- Smart-Meter-Messpunkten und den gemessenen Leitern;
- Archivierung, Verschieben, Typwechsel und Ersatz von Objekten;
- Bestandsmigrationen von 1.6.2 auf 1.6.3.

## Gefundene und korrigierte Fehlerklassen

### 1. Automatische Phasenschienen-Verbindungen

- Zulässige vorgelagerte Einspeisungen wie **FI/RCD → Phasenschiene** konnten
  von der Automatiksynchronisierung fälschlich als veraltete Schienenverbindung
  behandelt werden.
- Manuelle Verbindungen einer allgemeinen Sammelschiene zu Schutzgeräten konnten
  irrtümlich in die Kammschienen-Automatik geraten.
- Teilüberdeckungen und mehrere konkurrierende Phasenschienen waren nicht an
  allen Schreibwegen identisch abgesichert.

Korrektur: Automatisch verwaltet werden ausschließlich abgeleitete
**Phasenschiene → vollständig überdecktes Schutzgerät**-Verbindungen. Allgemeine
Sammelschienen und vorgelagerte Einspeisungen bleiben manuell und unangetastet.

### 2. Einheitliche Phasenberechnung

Die Berechnung der Außenleiter war zuvor auf mehrere Dienste verteilt. Dadurch
konnten Polzahl, Neutralleiterpol, Schienenstart und TE-Position unterschiedlich
interpretiert werden.

Korrektur: Eine gemeinsame Phasenkomponente berechnet das Muster für
Schrankansicht, Topologie, Automatiksynchronisierung und Migration. Bei RCD,
RCBO und SPD wird der Neutralleiterpol nicht als zusätzlicher Außenleiter
gezählt.

### 3. Stromkreis- und Verbraucherphasen

Ein Stromkreis konnte von einem L2-Schutzgerät versorgt werden, während eine
nachgelagerte Verbindung zum Verbraucher weiterhin als L1 dokumentiert wurde.

Korrektur: Stromkreise übernehmen eine eindeutige wirksame Außenleiterphase aus
Schutzgerät oder dokumentierter Einspeisung und geben sie verbindlich an
nachgelagerte Verbindungen weiter.

### 4. Smart-Meter-Messpunkte

Ein Messkanal konnte eine Phase auswählen, die auf der gemessenen Verbindung
nicht vorhanden war.

Korrektur: Messphasen werden gegen die wirksamen Leiter der Verbindung geprüft.
Bei genau einer wirksamen Außenleiterphase wird diese automatisch übernommen.
Beim Ersetzen einer automatischen Schienenverbindung bleiben Messpunkte erhalten
und werden korrekt umgehängt.

### 5. FI-, N- und PE-Beziehungen

- Eine N-Schiene konnte in einen anderen Komponententyp umgewandelt werden,
  obwohl Schutzgeräte sie noch referenzierten.
- FI/LS-Geräte konnten fälschlich wegen einer fehlenden separaten N-Schiene
  gewarnt werden.
- FI/RCD-Verweise waren nicht in allen Fällen auf fachlich passende
  Schienentypen begrenzt.

Korrektur: Typwechsel und Archivierung einer verwendeten N-Schiene sind
blockiert. Der RCBO-Sonderfall wird berücksichtigt. FI/RCD-Verweise sind nur an
Phasen- und N-Schienen erlaubt; PE-Schienen bleiben unabhängig.

### 6. Archivierung und Lebenszyklus

- Schutzgeräte konnten trotz aktiver manueller Zu- oder Abgangsverkabelung
  archiviert werden.
- Stromkreise konnten trotz aktiver Topologieverbindungen archiviert werden.
- Allgemeine Assets konnten trotz aktiver Elektroverbindungen archiviert,
  ersetzt oder an einen anderen Standort verschoben werden.
- Archivierte Stromkreise konnten aktive Asset-Zuordnungen hinterlassen.

Korrektur: Manuell dokumentierte Beziehungen müssen vor solchen Änderungen
bewusst gelöst werden. Nur automatisch abgeleitete Kammschienen-Verbindungen
werden intern synchronisiert.

### 7. Layout- und Platzierungsintegrität

Die Prüfungen für einfache Reihen, strukturierte Gerätebereiche und einzelne
Schreibwege waren nicht vollständig zentralisiert.

Korrektur: Kapazität, Bereichstyp, Kollision, vollständige Überdeckung,
Teilüberdeckung und konkurrierende Phasenschienen werden zentral validiert.
Eine Phasenschiene darf keine beliebigen DIN-Assets überdecken.

### 8. Datenbankintegrität und Bestandsreparatur

Migration `0043_release_1_6_3_electrical_integrity`:

- normalisiert Leiterfelder von Phasen-, N- und PE-Schienen;
- entfernt ungültige FI-Verweise und Phasenmetadaten anderer Komponententypen;
- rekonstruiert eindeutige automatische Kammschienen-Verbindungen;
- bewahrt legitime FI/RCD-Einspeisungen und manuelle Sammelschienen-Verbindungen;
- korrigiert nachgelagerte Außenleiter, Stromkreisverbindungen und Messphasen;
- ergänzt Datenbank-Constraints für Leiter, Phasenmetadaten und FI-Verweise.

## Erfolgreich ausgeführte Prüfungen

- zentrale Versionskonsistenz: `1.6.3`;
- Branding- und bestehende Korrekturverträge;
- neue Elektro-Integritäts- und Releaseverträge 1.6.3;
- Python-Syntax aller Backend-, Migrations-, Test- und Prüfscripte;
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten;
- Phasenschienen-Autoritätsprüfung;
- Migrationstests 0030, 0031, 0032, 0033, 0034, 0035, 0036, 0037,
  0039, 0040, 0041, 0042 und 0043;
- Migration 0043 einschließlich Upgrade, Datenreparatur, Constraints,
  Downgrade und erneutem Upgrade;
- finale ZIP-Kompressions-, Extraktions-, Versions- und Manifestprüfung.

## In dieser Build-Umgebung nicht ausführbare Gates

### Vollständige Backend-Pytest-Suite

Der Lauf wurde gestartet, brach aber bereits bei der Testsammlung ab, weil das
Python-Paket `sqlmodel` in der Umgebung nicht installiert ist:

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

### Vollständiger Frontend-Build und Vitest

`npm ci` wurde gestartet. Der interne Paketserver antwortete beim Abruf einer
transitiven Abhängigkeit mit HTTP 503:

```text
npm error code E503
npm error 503 Service Temporarily Unavailable
```

Daher konnten `vue-tsc --noEmit`, Vite-Build und Vitest nicht mit frisch
installierten Projektabhängigkeiten ausgeführt werden. Die dependency-freie
TypeScript-/Vue-Syntaxprüfung war erfolgreich.

### Docker-Build

Docker ist in der Build-Umgebung nicht installiert (`docker: command not found`).
Ein Containerstart und Laufzeittest muss daher auf dem Zielsystem erfolgen.

## Updateprüfung auf dem Zielsystem

Vor dem Update ist der persistente `data`-Ordner vollständig zu sichern.
Anschließend:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs -f jarvis
```

Im Log muss das Alembic-Upgrade `0042 -> 0043` erfolgreich durchlaufen. Danach
Browsercache vollständig aktualisieren.

## Ergebnis

Die dependency-frei ausführbaren Prüfungen und sämtliche vorhandenen
Migrationsprüfungen waren erfolgreich. Die gefundenen systemischen Fehler im
Elektro-Modul wurden in Quellcode, Datenmodell, Migration, Frontendverhalten und
Dokumentation gemeinsam korrigiert. Die oben ausdrücklich genannten
abhängigkeits- und Docker-basierten Gates bleiben auf dem Zielsystem auszuführen.
## Nachträgliche Frontend-Build-Korrektur

Der beim Docker-Build gemeldete TypeScript-Fehler in
`frontend/src/pages/phaseRailAutoWiring.test.ts` wurde nachvollzogen. Ursache war ein
Import aus `node:fs`, obwohl der Frontend-`tsconfig.json` ausschließlich Browser-/Vite-Typen
lädt. Der Test verwendet nun denselben `?raw`-Import wie die bereits vorhandenen
Quellvertragstests. Zusätzlich prüft `scripts/check-release-1.6.3.py`, dass weder
`node:fs` noch `readFileSync` dort erneut eingeführt werden.

Ein vollständiger lokaler Wiederholungslauf von `npm run build` war in dieser Umgebung
nicht möglich, weil der interne npm-Paketserver beim Nachladen der Abhängigkeiten HTTP 503
lieferte. Der ursprüngliche Fehlerpfad wurde jedoch direkt beseitigt; alle anderen
Frontend-Quellvertragstests im Projekt verwenden bereits erfolgreich das gleiche
`?raw`-Muster.

## Nachprüfung: Drag-and-drop, Archivierung und automatische Kontakte

Nach Rückmeldung aus dem produktiven Docker-Build wurden drei zusätzliche
End-to-End-Pfade erneut untersucht:

1. Verschieben von Schutzgeräten innerhalb einer Phasen-/Kammschiene;
2. Archivieren direkt aus der Detailseitenleiste;
3. Erzeugung und Wiederherstellung der abgeleiteten Verbindung
   **Phasenschiene → Schutzgerät**.

### Gefundene Ursachen

- Die Oberfläche behandelte Phasenschienen beim Drag-and-drop für Schutzgeräte
  und allgemeine DIN-Assets gleich. Der Server unterschied korrekt, die
  Frontend-Vorprüfung übersprang die fachliche Unterscheidung jedoch vollständig.
  Das führte bei einem allgemeinen DIN-Asset erst nach dem Drop zu einer wenig
  verständlichen Servermeldung.
- Die Archivierungsfunktionen waren zwar in einzelnen Karten vorhanden, fehlten
  jedoch in der zentralen Detailseitenleiste.
- Die Automatiksynchronisierung konnte direkt vor dem Commit auf noch nicht
  geflushte Änderungen treffen. Außerdem bestand für einen bereits fehlerhaften
  Bestandsstand kein selbstheilender Abgleich beim Öffnen der Topologie.

### Korrekturen

- Vollständig von einer Phasenschiene überdeckte Schutzgeräte dürfen wieder
  verschoben werden. Teilüberdeckungen bleiben gesperrt.
- Allgemeine DIN-Assets werden unter einer Phasenschiene weiterhin bewusst
  abgewiesen; die Meldung bezeichnet das gezogene Objekt nun ausdrücklich als
  allgemeines DIN-Asset.
- Schutzgeräte und Schrankkomponenten besitzen in der Detailseitenleiste eine
  Archivieren-Aktion. Fehler werden innerhalb der Detailansicht angezeigt.
- Beim Archivieren einer Phasenschiene bleiben die Schutzgeräte platziert. Alle
  aktiven Verbindungen der Schiene werden atomar historisch archiviert.
- Die Synchronisierung flusht neue oder verschobene Schienen und Schutzgeräte,
  bevor die Kontaktverbindungen abgeleitet werden.
- Topologie und Verbindungsliste führen einen selbstheilenden Abgleich aktiver
  Phasenschienen aus. Fehlende abgeleitete Kontakte werden rekonstruiert und
  konkurrierende manuelle Einspeisungen des Schutzgeräts sauber ersetzt.
- Der stabile Abgleich ist idempotent und verändert Zeitstempel nur bei einer
  tatsächlichen fachlichen Änderung.

### Ausgeführte Prüfungen

- Python-Syntaxprüfung für Anwendung, Migrationen und Tests;
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten;
- Versions-, Branding-, gesammelte Fixes-, Ableseerinnerungs-,
  Phasenschienen- und Elektro-Integritätsverträge;
- alle dependency-freien Migrationsprüfungen 0030 bis 0043;
- ergänzte Regressionstestquellen für Selbstheilung und Archivierung einer
  belegten Phasenschiene;
- Quellvertragstest für Detail-Archivierung und korrekte DnD-Unterscheidung.

### Nicht erneut vollständig ausführbar

Die vollständige SQLModel/Pytest-Suite konnte nicht gestartet werden, da die
Python-Abhängigkeiten in der isolierten Build-Umgebung nicht verfügbar waren.
`npm ci` konnte ebenfalls keine vollständigen Pakete beziehen; daher waren
`vue-tsc`, Vitest und Vite hier nicht erneut ausführbar. Der vom vorherigen
Release bekannte Node-Builtin-Import ist weiterhin entfernt. Alle geänderten
Dateien wurden mit den verfügbaren dependency-freien Syntax- und
Vertragsprüfungen geprüft.

## 1.6.2 – 2026-07-27

### Changelog

- automatische Verbindungen zwischen Phasen-/Kammschiene und allen überspannten
  Schutzgeräten; Synchronisierung bei späterer Platzierung und Verschiebung
- FI/RCD-Zuordnung an Phasen-/Kammschienen als optional klargestellt; falsche
  Warnung bei fehlender Zuordnung entfernt

- Phasenschienen-Verbindungen sind im Bearbeitungsdialog vollständig gesperrt:
  L1/L2/L3 werden nicht mehr als auswählbare Optionen angezeigt; nur N und PE
  können ergänzt werden. Direkte Verbindungen Phasenschiene ↔ Schutzgerät werden
  auch serverseitig aus Startphase und TE-Position berechnet.
- Migration `0041` repariert vorhandene falsche Außenleiterwerte auch auf
  Installationen, die Migration `0040` bereits ausgeführt hatten.
### Behoben

- monatliche Zählerpläne erzeugen idempotente Aufgaben und werden durch eine
  gespeicherte Ablesung automatisch abgeschlossen;
- PV-Erzeugung und Netzeinspeisung sind im Dashboard getrennt und nur bei
  ausgewählten Zählern sichtbar;
- Topologieansichten verwenden wirksame Phasen und kennzeichnen alte
  Abweichungen, statt sie still auszublenden;
- GitHub-/Release-/Support-Verweise bleiben in lokalen und offiziellen ZIPs
  erhalten.
- Verteilerdosen werden im Dialog zur fortlaufenden DIN-Serienplatzierung
  ausgeschlossen; dadurch ist der Vue-TSC-Build wieder typkonsistent.
- Kamm-/Phasenschienen können bestehende Schutzgeräte und normale
  DIN-Asset-Platzierungen überspannen, ohne eine TE-Kollision auszulösen. Nur
  überlappende Schienen auf derselben Montageseite werden abgewiesen.
- Verkabelungen an Schutzgeräten unter einer Sammel-/Phasenschiene übernehmen
  die aus Schienenstart und TE-Position berechnete Phase automatisch. Eine freie
  abweichende Auswahl von L1/L2/L3 ist im Dialog und über die API ausgeschlossen.
- Fehler beim Speichern von Schrankkomponenten und Versorgungsverbindungen werden
  im jeweils geöffneten Dialog angezeigt und nicht mehr hinter dem Overlay.
- Migration `0040` verwendet für den Archivstatus von Schutzgeräten die
  zugehörige Basistabelle `electrical_components`. Dadurch läuft das Upgrade auch
  auf bestehenden 1.6.1/1.6.2-Datenbanken ohne nicht vorhandene `deleted_at`-Spalte.

### Hinzugefügt

- Verteilerdose als struktureller Behälter ohne sichtbares TE-Raster;
- Kamm-/Phasenschienen als TE-freies Overlay mit Montage oberhalb/unterhalb;
- Migration `0039_release_1_6_2_integrity`;
- paketfeste Projektmetadaten in `SOURCE_INFO.json`.

### Release Notes

Veröffentlicht: 27. Juli 2026

DocOfHome 1.6.2 baut auf Version 1.6.1 auf und schließt die im Korrektur-Runbook
noch offenen Integritäts- und Bedienlücken. Bestehende Daten werden nicht
stillschweigend umgeschrieben.

## Wichtigste Änderungen

- Aktive monatliche Zählerpläne erzeugen genau eine automatisch verwaltete
  Aufgabe pro Zähler und Monat. Eine gespeicherte Ablesung erledigt die Aufgabe;
  deaktivierte Pläne erzeugen keine neue Aufgabe.
- Das Dashboard unterscheidet **PV-Erzeugung** und **PV eingespeist**. Beide
  Kacheln erscheinen nur, wenn ein passender dashboardrelevanter Zähler vorhanden
  ist; mehrere ausgewählte PV-Zähler werden gemeinsam ausgewertet.
- Die elektrische Topologie liefert neben den gespeicherten auch die wirksamen
  Phasen. Alte Widersprüche bleiben sichtbar und erhalten eine Warnung, während
  neue Verbindungen an einphasigen Schutzgeräten nur die berechnete Phase
  akzeptieren.
- Haupt-/Unterverteilungen werden als strukturelle Behälter behandelt. Neue
  Verkabelungen werden an enthaltenen Einbaugeräten und Klemmen dokumentiert.
- Der Aufbau **Verteilerdose** steht für Verbindungsklemmen ohne sichtbares
  Reihen- oder TE-Raster zur Verfügung.
- Kamm-/Phasenschienen werden als Overlay über beziehungsweise unter
  Schutzgeräten dargestellt, belegen selbst keine TE und können nicht archiviert
  werden, solange sie noch Schutzgeräte überdecken.
- Repository-, Release- und Support-Verweise sind fest im Quellstand und in
  `SOURCE_INFO.json` enthalten; sie bleiben deshalb auch außerhalb einer
  `.git`-Arbeitskopie erhalten.
- Der Duplizier-/Seriendialog bietet für die fortlaufende DIN-Platzierung nur
  Verteilungen mit Reihen- oder Bereichslayout an. Verteilerdosen werden dort
  ausgeschlossen, wodurch der TypeScript-Fehler beim Docker-Frontend-Build
  behoben ist.
- Kamm-/Phasenschienen werden bei der Platzierungsprüfung nun konsequent als
  Anschlusskomponenten ohne eigene TE-Belegung behandelt. Sie dürfen bestehende
  Schutzgeräte und normale DIN-Assets überspannen. Eine Überschneidung wird nur
  noch zwischen Schienen auf derselben Montageebene oberhalb beziehungsweise
  unterhalb blockiert.
- Liegt ein Schutzgerät unter einer Sammel-/Phasenschiene, wird seine wirksame
  Außenleiterphase im Verkabelungsdialog automatisch aus Position und Startphase
  der Schiene übernommen. L1/L2/L3 können dort nicht mehr manuell abweichend
  gewählt werden; N und PE bleiben auswählbar. Das Backend erzwingt dieselbe
  Zuordnung auch für direkte API-Aufrufe und korrigiert eine alte Abweichung beim
  nächsten Speichern der Verbindung.
- Validierungsfehler beim Bearbeiten von Schrankkomponenten und elektrischen
  Verbindungen erscheinen innerhalb des geöffneten Dialogs statt verdeckt im
  Seitenhintergrund.
- Der Bearbeitungsdialog zeigt bei einer Verbindung zwischen Phasenschiene und
  Schutzgerät keine auswählbaren Außenleiter mehr. Die berechnete Phase wird als
  gesperrter Wert angezeigt; ausschließlich N und PE bleiben ergänzbar. Auch bei
  fehlenden Phasenmetadaten bleibt Speichern gesperrt, statt auf eine freie
  Phasenauswahl zurückzufallen.
- Das Backend berechnet die Phase einer direkten Verbindung
  Phasenschiene → Schutzgerät zusätzlich aus den tatsächlich gespeicherten
  Schienen- und Gerätepositionen. Ein manuell übermitteltes L1/L2/L3 wird beim
  Speichern verbindlich durch die Positionsphase ersetzt.

- Phasen-/Kammschienen erzeugen ihre physisch zwingenden Verbindungen zu allen
  bereits vorhandenen und später platzierten Schutzgeräten automatisch. Die
  Verbindungen werden bei Verschieben, Polzahländerung oder Änderung des
  Schienenbereichs aktualisiert.
- Die Zuordnung zu einem FI/RCD ist bei einer Phasen-/Kammschiene ausdrücklich
  optional. Eine fehlende FI-Zuordnung erzeugt keine Warnung mehr.
- Der Startfehler der Migration `0040` auf vorhandenen Datenbanken ist behoben.
  Schutzgeräte besitzen selbst keine Spalte `deleted_at`; der aktive Zustand wird
  nun korrekt über `electrical_components.deleted_at` ermittelt.

## Datenbank

Alembic-Migration `0039`:

- ergänzt den eindeutigen Automationsschlüssel für erzeugte Ableseaufgaben;
- ergänzt die Montageposition `above`/`below` für Kamm-/Phasenschienen;
- erlaubt den Verteilungsaufbau `junction_box`.

Alembic-Migration `0040`:

- trennt allgemeine Sammelschienen von positionsgebundenen Phasenschienen;
- repariert eindeutige bestehende Phasenzuordnungen;
- ermittelt aktive Schutzgeräte über die Basistabelle `electrical_components` und
  funktioniert damit mit dem tatsächlich vorhandenen Datenbankschema.

Alembic-Migration `0041`:

- repariert bestehende Verbindungen nach bereits ausgeführter Migration `0040`
  erneut anhand der tatsächlichen Phasenschienen- und TE-Positionen;
- ist erforderlich, weil Installationen, die bereits auf Alembic-Head `0040`
  stehen, die korrigierte Reparaturlogik sonst nicht erneut ausführen würden.

Alembic-Migration `0042`:

- legt für alle von einer Phasen-/Kammschiene überspannten Schutzgeräte die
  physische Verbindung automatisch an;
- korrigiert die Phase anhand von Startphase und TE-Position;
- entfernt veraltete oder umgekehrt gerichtete direkte Schienenverbindungen;
- benötigt keine FI/RCD-Zuordnung.

Die Migration ersetzt keine vorhandenen Zählerstände, Assets, Bilder,
Dokumente oder Verkabelungen. Vor dem Update ist trotzdem ein vollständiges
Backup des persistenten `data`-Ordners erforderlich.

## Update von 1.6.1

1. In DocOfHome ein Backup erstellen und den persistenten `data`-Ordner extern sichern.
2. Container stoppen: `docker compose down`.
3. Version 1.6.2 in einen neuen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. `docker compose build --no-cache` und `docker compose up -d` ausführen.
6. Prüfen, dass die Migrationen `0039`, `0040`, `0041` und `0042` erfolgreich ausgeführt wurden.
7. Aufgaben, Zähler-Dashboard, Topologie und Verteilerdosen praktisch prüfen.

### Validierung

Stand: 27. Juli 2026

## Gegenstand dieser Korrektur

Die Phasen-/Kammschiene war im Schrankplan zwar sichtbar, ihre physisch zwingenden
Kontakte zu den überspannten Sicherungsautomaten mussten aber weiterhin manuell als
Versorgungsverbindungen angelegt werden. Außerdem wurde eine fehlende FI/RCD-Zuordnung
fälschlich als Warnung dargestellt, obwohl Kammschienen auch ohne FI/RCD eingesetzt
werden können.

## Umsetzung

- Neue zentrale Synchronisierung `PhaseRailConnectionService`.
- Beim Anlegen oder Ändern einer Phasen-/Kammschiene werden Verbindungen zu allen
  bereits platzierten und überspannten Schutzgeräten automatisch angelegt.
- Wird ein Schutzgerät später unter der Schiene platziert oder verschoben, wird die
  Verbindung automatisch erstellt, korrigiert oder archiviert.
- Die Außenleiterphase wird ausschließlich aus Startphase, Schienenstart und
  TE-Position berechnet.
- Direkte automatische Schienenverbindungen enthalten nur L1/L2/L3. N und PE werden
  separat dokumentiert.
- Automatische Schienenverbindungen können in der Topologie weder gelöscht noch auf
  andere Endpunkte oder Verbindungsarten umgehängt werden.
- Eine FI/RCD-Zuordnung ist bei einer Phasen-/Kammschiene optional. Die bisherige
  Warnung bei fehlender Zuordnung wurde entfernt und der Dialogtext klargestellt.
- Migration `0042` legt fehlende Verbindungen für bestehende Installationen an,
  korrigiert falsche Phasen und archiviert veraltete beziehungsweise umgekehrte
  direkte Schienenverbindungen.

## Erfolgreiche Prüfungen

- Python-Syntaxprüfung der Anwendung, Migrationen, Tests und Prüfscripte
- TypeScript-Syntaxprüfung der geänderten Vue-/Test-Scripte mit dem lokalen
  TypeScript-Parser
- Versions- und Brandingprüfung
- gesammelte Korrekturverträge und Releasevertrag 1.6.2
- dependency-freier Phasenschienen-Vertragstest
- ZIP-Kompressions- und Extraktionsprüfung

## Nicht vollständig ausgeführte Gates

Die vollständige Python-Test- und Alembic-Suite konnte in dieser Umgebung nicht
abhängigkeitsbasiert ausgeführt werden, weil die erforderlichen Python-Pakete nicht
über den Paketindex verfügbar waren. `npm ci` konnte ebenfalls nicht vollständig
abgeschlossen werden; deshalb wurden Vue-TSC, Vite und Vitest nicht vollständig
neu ausgeführt. Die entsprechenden Regressionstests und Prüfscripte sind im Paket
enthalten.

## Alembic-Head

`0042`

## 1.6.1 – 2026-07-27

### Changelog

### Geändert

- Zählerwechsel ist ein eigener atomarer Vorgang; normale Ablesungen enthalten
  keine Reset-Option mehr und zeigen den letzten Stand sowie passende
  OBIS-Hinweise.
- Mehrere ausgewählte PV-Zähler werden im Dashboard gemeinsam ausgewertet.
- Online-Produktbildquellen sind einzeln konfigurierbar; Ergebnisse aktivierter
  Quellen werden kombiniert, dedupliziert und nach Relevanz sortiert.
- Asset-Details zeigen direkte elektrische Einspeisungen und Weiterführungen.
  Versorgungswege ab Phasenverteilerblock werden vollständig und in
  Anschlussreihenfolge nach L1, L2, L3, mehrphasig und nicht zugeordnet
  dargestellt – sowohl in der Elektro-Topologie als auch direkt in der
  Zähler-/Sicherungsschrankansicht. Fehlende Phasenangaben, Phasenwechsel und
  Zyklen werden sichtbar gekennzeichnet.
- Ein-TE-Geräte und -Assets erhalten in der kompakten Schrankansicht eine
  zuverlässige, vollständig lesbare Hochkantbeschriftung; technische Kurzwerte
  wie `B16` bleiben separat horizontal sichtbar.
- Sicherungs-/Schutzgeräte werden zentral klassifiziert und einheitlich gezählt.
- Netzwerkschnittstellen können als primär markiert werden.

### Hinzugefügt

- ausführliche Hilfetexte zur Energiebilanz;
- Home-Assistant-Rollen für Schaltausgang, Eingang, Verfügbarkeit und Diagnose;
- Standard-Asset-Typ **Smartes Relais / DIN-Schaltaktor** und Produkt
  **Shelly Pro 1**;
- Migration `0038_release_1_6_1_corrections`.

### Release Notes

Veröffentlicht: 27. Juli 2026

DocOfHome 1.6.1 setzt die im Korrektur-Runbook vom 27. Juli 2026 beschriebenen
Anpassungen um. Der Schwerpunkt liegt auf klaren Zählerabläufen, einer
vollständigeren PV-Auswertung und konsistenter technischer Dokumentation.

## Wichtigste Änderungen

- Der Zählerwechsel ist vom normalen Ablesen getrennt. Schlussstand,
  Austauschzeitpunkt, neue Zählernummer und Startstand werden gemeinsam und
  atomar gespeichert.
- Der Ablesedialog zeigt den letzten Stand. Für Netzbezug und Einspeisung werden
  die üblichen OBIS-Kennzahlen 1.8.0 beziehungsweise 2.8.0 erläutert.
- Mehrere PV-Erzeugungszähler können gleichzeitig dashboardrelevant sein; ihre
  Werte werden für Periodenvergleiche zusammengeführt.
- Wikimedia Commons und DuckDuckGo Images lassen sich einzeln aktivieren. Das
  Backend setzt diese Auswahl durch und führt relevante Treffer zusammen.
- Direkte elektrische Verbindungen werden am Asset angezeigt. Ab einem
  Phasenverteilerblock sind die vollständigen Versorgungswege bis zum jeweiligen
  Endpunkt in Anschlussreihenfolge nach L1, L2, L3, mehrphasig und nicht
  zugeordnet gruppiert. Die Wege sind in der Elektro-Topologie und direkt im
  Zähler-/Sicherungsschrank aufklappbar; fehlende Phasenangaben, Phasenwechsel
  und Zyklen werden gekennzeichnet.
- In der kompakten Zähler-/Sicherungsschrankansicht werden Namen von Geräten mit
  einer Teilungseinheit vollständig hochkant dargestellt; Kurzwerte wie `B16`
  bleiben am Kartenfuß horizontal lesbar.
- Schutzgeräte werden über eine zentrale Klassifikation erkannt, auch wenn sie
  als allgemeine DIN-Platzierung dokumentiert sind.
- Netzwerkschnittstellen besitzen eine eindeutige primäre Schnittstelle je Gerät.
- Smarte Relais/DIN-Schaltaktoren erhalten passende Stammdaten und
  Home-Assistant-Rollen.

## Datenbank

Alembic-Migration `0038`:

- ergänzt Einstellungen für die beiden Produktbildquellen;
- ergänzt die primäre Netzwerkschnittstelle;
- erweitert zulässige Home-Assistant-Rollen;
- erlaubt mehrere primäre PV-Dashboardzähler;
- legt Standarddaten für **Smartes Relais / DIN-Schaltaktor** und
  **Shelly Pro 1** an.

Bestehende Daten werden nicht ersetzt. Vor dem Update ist wie üblich ein
vollständiges Backup des persistenten `data`-Ordners erforderlich.

## Update von 1.6.0

1. Backup erstellen und `data` zusätzlich extern sichern.
2. Container stoppen.
3. 1.6.1 in einen neuen Ordner entpacken und lokale Konfiguration übernehmen.
4. Images neu bauen und Container starten.
5. Prüfen, dass Migration `0038` erfolgreich ausgeführt wurde.

Das Quellpaket enthält weder Laufzeitdaten noch Zugangsdaten.

## 1.6.0 – 2026-07-27

### Changelog

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

### Release Notes

Veröffentlicht: 27. Juli 2026  
Alembic-Head: `0037`

## Schwerpunkte

DocOfHome 1.6.0 korrigiert den Einrichtungsassistenten, benennt neue Backups
konsistent, verbessert die Online-Produktbildsuche und richtet die optische
Sicherungs-/Zählerschrankansicht stärker auf PC und Tablet aus.

Sicherungsautomaten erhalten optionale Stammdaten für Auslösecharakteristik und
Nennstrom. Der empfohlene Typ Stromstoßschalter bringt zusätzlich Spulenspannung,
Spannungsart, Kontaktanzahl und Kontaktart mit. Smart Meter
können mehrere CT-/Stromwandlerklemmen als nicht leitende Messpunkte an
vorhandenen elektrischen Verbindungen dokumentieren. Jeder Messpunkt kann eigene
Home-Assistant-Entitäten besitzen.

## Wichtige Änderungen

- Integrationsstatus wird beim Wechsel des Assistentenschritts gelöscht.
- Nach dem geführten Setup wird das gespeicherte Asset geöffnet; zusätzlich
  steht **Zur Übersicht** zur Verfügung.
- Neue Backups heißen `DocOfHome-backup-*`; `tectoryn-backup-*` bleibt lesbar.
- DuckDuckGo Images ist primäre Bildquelle, Wikimedia Commons der Fallback.
- Wasser- und Gaszähler werden im elektrischen Zählerfeld nicht angeboten.
- DIN-Geräte zeigen im Kompaktmodus primär den Namen, optional Livewert oder
  technische Kurzangabe wie B16.
- Farben und Legende unterscheiden zentrale Gerätetypen.
- Handbuch erklärt Sammelschiene, Kammschiene und CT-Klemmen ausführlicher.

## Datenbank

Migration `0037_release_1_6_electrical_measurements` ergänzt:

- `breaker_characteristic` und `rated_current_a` an Asset-Typen und Assets;
- `coil_voltage_v`, `coil_voltage_type`, `contact_count` und `contact_type` an
  Asset-Typen und Assets;
- `smart_meter_measurement_points`;
- `smart_meter_measurement_entities`.

Neue Felder sind optional. Bestehende Datensätze bleiben gültig.

## Sicherheit

CT-Klemmen werden ausschließlich als Messbeziehung modelliert und erzeugen
keine stromführende Verbindung. Arbeiten und Änderungen an elektrischen Anlagen
gehören in die Hände einer Elektrofachkraft.

## Prüfung

Tatsächlich ausgeführte und nicht ausführbare Prüfungen sind im beiliegenden
`DocOfHome-1.6.0-VALIDATION.md` und in
`docs/VALIDATION_REPORT_1.6.0.md` dokumentiert.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.6.0.md

**Stand:** 27. Juli 2026  
**Ausgangsbasis:** `DocOfHome-1.5.0.zip`  
**Zielversion:** `1.6.0`  
**Alembic-Head:** `0037`

## Zusammenfassung

Der Quellstand wurde statisch geprüft und die Migrationen wurden isoliert gegen
SQLite ausgeführt. Die neuen Releaseverträge, die Python-Compileprüfung und die
Syntaxprüfung der geänderten TypeScript- beziehungsweise Vue-Scriptblöcke sind
erfolgreich.

Die vollständigen Frontend-, Backend- und Docker-Gates konnten in der
Arbeitsumgebung nicht ausgeführt werden, weil benötigte Pakete nicht vom
internen Paketproxy geladen werden konnten und kein Docker-Programm vorhanden
war. Sie werden daher ausdrücklich **nicht als bestanden** bewertet.

Der bereitgestellte Stand ist damit ein statisch und migrationsseitig geprüfter
Quellrelease. Vor einer produktiven Aktualisierung müssen die offenen Gates auf
einem Buildsystem mit funktionierenden Paketquellen und Docker nachgeholt
werden.

## Erfolgreich ausgeführte Prüfungen

### Projekt- und Versionsverträge

- zentrale Version `1.6.0` in `VERSION`;
- Backend-Paketversion `1.6.0`;
- eigene Frontend-Paketmetadaten `1.6.0`;
- transitive npm-Abhängigkeiten nicht pauschal versioniert;
- Alembic-Head ist Migration `0037`;
- sichtbarer Produktname mit `scripts/check-branding.py` geprüft;
- `git diff --check` ohne Whitespacefehler.

### Python und Releaseverträge

Ausgeführt:

```text
python3 -m compileall -q backend scripts
python3 scripts/check-branding.py
python3 scripts/check-release-1.2.4.py
python3 scripts/check-release-1.3.0.py
python3 scripts/check-release-1.3.1.py
python3 scripts/check-release-1.3.2.py
python3 scripts/check-release-1.4.0.py
python3 scripts/check-release-1.4.1.py
python3 scripts/check-release-1.4.2.py
python3 scripts/check-release-1.5.0.py
python3 scripts/check-release-1.6.0.py
```

Ergebnis: erfolgreich.

Der Releasevertrag 1.6.0 prüft unter anderem:

- Zurücksetzen der Integrationsmeldung im Assistenten;
- Abschlussnavigation und manuellen Fallback;
- neuen Backup-Präfix und Legacy-Kompatibilität;
- DuckDuckGo-/Wikimedia-Bildsuche;
- Filterung nicht elektrischer Zähler;
- kompakte Schrankansicht und Asset-Typ-Farben;
- Sicherungsautomat- und Stromstoßschalter-Stammdaten;
- Smart-Meter-Messpunkte und Home-Assistant-Zuordnungen;
- Handbucherweiterungen.

### Migrationen

Ausgeführt:

```text
python3 scripts/check-migration-0030.py
python3 scripts/check-migration-0031.py
python3 scripts/check-migration-0032.py
python3 scripts/check-migration-0033.py
python3 scripts/check-migration-0034.py
python3 scripts/check-migration-0035.py
python3 scripts/check-migration-0036.py
python3 scripts/check-migration-0037.py
```

Ergebnis: erfolgreich.

Migration `0037` wurde isoliert als Upgrade, Downgrade und erneutes Upgrade
geprüft. Sie ergänzt optionale Felder für Sicherungsautomaten und
Stromstoßschalter sowie neue Tabellen für CT-/Smart-Meter-Messpunkte. Bestehende
Datensätze werden nicht überschrieben.

### TypeScript- und Vue-Script-Syntax

Die geänderten `.ts`-Dateien und die `<script setup lang="ts">`-Blöcke der
geänderten Vue-Komponenten wurden mit TypeScript `transpileModule` syntaktisch
geprüft.

Ergebnis: erfolgreich.

Diese Prüfung ersetzt weder `vue-tsc --noEmit` noch die Vue-Template-Kompilierung
oder Vitest.

## Nicht vollständig ausführbare Prüfungen

### Frontend: npm, Vitest, vue-tsc und Vite

`npm ci --offline` wurde ausgeführt und scheiterte, weil das benötigte Paket
`why-is-node-running-2.3.0.tgz` nicht im lokalen Cache vorhanden war:

```text
npm error code ENOTCACHED
npm error request to .../why-is-node-running-2.3.0.tgz failed:
cache mode is 'only-if-cached' but no cached response is available.
```

Der interne npm-Paketproxy antwortete für dieses Paket zusätzlich mit HTTP 503.
Daher konnten folgende Prüfungen nicht zuverlässig gestartet werden:

```text
npm test
npm run build
vue-tsc --noEmit
vite build
```

Bewertung: **nicht ausgeführt / nicht bestanden behauptet**.

### Backend: Entwicklungsabhängigkeiten, Ruff, Mypy und Pytest

Die Installation aus `backend/requirements-dev.txt` scheiterte am internen
Python-Paketindex:

```text
ERROR: Could not find a version that satisfies the requirement
fastapi<0.117,>=0.116 (from versions: none)
ERROR: No matching distribution found for fastapi<0.117,>=0.116
```

In der vorhandenen globalen Python-Umgebung fehlten unter anderem `sqlmodel`,
`apscheduler`, `structlog`, `ruff` und `mypy`. Deshalb konnten folgende Gates
nicht vollständig ausgeführt werden:

```text
ruff check app tests
mypy app
python -m pytest -q
alembic upgrade head
alembic check
```

Die migrationsspezifischen SQLite-Prüfskripte liefen unabhängig davon
vollständig erfolgreich.

Bewertung der vollständigen Backend-Suite: **nicht ausgeführt / nicht bestanden
behauptet**.

### Docker

In der Arbeitsumgebung ist kein Docker-Programm installiert:

```text
bash: docker: command not found
```

Daher nicht ausgeführt:

```text
docker compose build --no-cache
docker compose up -d
Healthcheck
Logprüfung
praktische Browserprüfung im Container
```

Bewertung: **nicht ausgeführt / nicht bestanden behauptet**.

## Vor produktivem Einsatz nachzuholen

Auf einem geeigneten Buildsystem aus dem frisch entpackten Releasebestand:

```bash
cd frontend
npm ci
npm test
npm run build

cd ../backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/python -m pytest -q

cd ..
bash scripts/check.sh
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --no-color
```

Danach praktisch prüfen:

- Integrationsmeldungen beim Schrittwechsel;
- Abschluss des geführten Assistenten und Fallback-Button;
- Backup-Erstellung mit DocOfHome-Namen sowie Restore eines alten
  `tectoryn-backup-*`-Archivs;
- Online-Bildsuche mit realen Hersteller-/Modellbezeichnungen;
- Zählerschrank auf PC und Tablet;
- Filterung von Wasser- und Gaszählern;
- B16-/C16-Stammdaten und Stromstoßschalter;
- Smart-Meter-Messklemmen, Verkabelungszuordnung und Home-Assistant-Entitäten;
- bestehende Verteilungen, Verkabelungen, Bilder und Zählerstände nach Migration.
## 1.5.0 – 2026-07-26

### Changelog

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

### Release Notes

Stand: 26. Juli 2026  
Alembic-Head: `0036`

## Neu

- statische, vollständig offline nutzbare Seite **Wiki → Handbuch & Glossar**;
- 109 verständlich erklärte Begriffe aus Einstieg, Assets, Elektro, Netzwerk,
  Verbrauch, Home Assistant, Bildern/Dokumenten sowie Backup/Betrieb;
- zentrale Frontend-Datenstruktur ohne neue Datenbanktabelle oder Migration;
- Suche über Begriff, Alias, Beschreibung, Beispiel, Kategorie und verwandte
  Begriffe;
- Kategorienfilter und alphabetisches Glossar mit A–Z-Sprungmarken;
- einklappbare Handbuchabschnitte, Inhaltsverzeichnis und interne Ankerlinks;
- responsive Darstellung mit mobilem Inhaltsverzeichnis und großen Touch-Zielen;
- verbindlicher Hinweis, dass Änderungen an elektrischen Anlagen in die Hände
  einer Elektrofachkraft gehören.

## Elektro-Detailansicht

- platzierte Schutzgeräte und andere DIN-Assets besitzen nun den gut sichtbaren
  Button **Asset bearbeiten**;
- **Position bearbeiten** beziehungsweise **Position / Gruppe** bleibt erhalten;
- reine passive Schrankkomponenten zeigen weiterhin keinen Asset-Button;
- die normale Asset-Bearbeitungsseite wird verwendet, damit keine zweite
  Bearbeitungslogik entsteht.

## Kompatibilität und Daten

- keine neue Datenbankmigration; Alembic-Head bleibt `0036`;
- bestehende Wiki-Seiten bleiben editierbar und unverändert unter `/wiki`;
- das Handbuch liegt unter `/wiki/handbuch` und benötigt weder API noch Internet;
- bestehende Assets, Produkte, Verteilungen, Zähler, Netzwerkdaten,
  Home-Assistant-Zuordnungen, Verkabelungen und Bilder bleiben unverändert.

## Prüfung

Der tatsächliche Prüfstatus ist im Release-Artefakt
`DocOfHome-1.5.0-VALIDATION.md` und in
`docs/VALIDATION_REPORT_1.5.0.md` dokumentiert. Nicht ausgeführte oder durch die
Arbeitsumgebung blockierte Prüfungen werden dort ausdrücklich als offen
gekennzeichnet.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.5.0.md

Stand: 26. Juli 2026  
Ausgangsbasis: `DocOfHome-1.4.2-r3.zip`  
Zielversion: DocOfHome 1.5.0  
Alembic-Head: `0036`

## 1. Umgesetzter Umfang

- statische Route `/wiki/handbuch` unter der Navigation **Wiki**;
- bestehende editierbare Wiki-Seiten unverändert unter `/wiki`;
- zentrale Frontend-Datenstruktur mit 109 Begriffen in acht Kategorien;
- lokale Suche über Begriff, Alias, Beschreibung, Beispiel, Kategorie und
  verwandte Begriffe;
- Kategorienfilter, einklappbare Handbuchabschnitte, Inhaltsverzeichnis,
  interne Ankerlinks und Glossar A–Z;
- responsive Desktop- und Mobilstruktur ohne Backend- oder Internetabhängigkeit;
- Elektro-Sicherheitshinweis;
- Button **Asset bearbeiten** bei Schutzgeräten und normalen DIN-Assets;
- kein Asset-Button bei passiven Schrankkomponenten;
- keine Datenbankmigration; Alembic-Head bleibt `0036`.

## 2. Tatsächlich erfolgreich ausgeführte Prüfungen

- `python scripts/check-version.py`;
- `python scripts/check-branding.py`;
- `python scripts/check-collected-fixes.py`;
- `python scripts/check-reading-reminders.py`;
- alle statischen Releaseverträge von 1.2.4 bis 1.5.0;
- `python -m compileall -q backend/app backend/migrations backend/tests scripts`;
- TypeScript-Compile-Prüfung der zentralen Handbuch-Datenstruktur mit globalem
  TypeScript 5.8.3;
- ausgeführte JavaScript-Laufzeitprüfung der kompilierten Handbuchlogik:
  109 Begriffe, Suche nach DHCP und Kammschiene sowie A–Z-Sprungmarken;
- Prüfung, dass `frontend/package-lock.json` gegenüber 1.4.2-r3 ausschließlich
  die beiden eigenen Versionsfelder von 1.4.2 auf 1.5.0 ändert;
- Prüfung, dass die transitive Abhängigkeit `rfdc` unverändert auf 1.4.1 bleibt;
- statische Prüfung der Route, Navigation, zentralen Begriffe, mobilen Struktur
  und beiden Asset-Bearbeitungswege;
- statische Prüfung, dass der Detailblock passiver Schrankkomponenten keinen
  Button **Asset bearbeiten** enthält.

## 3. Blockierte oder nicht ausführbare Prüfungen

### Frontend: npm, Vitest, vue-tsc und Vite

`npm ci` wurde zweimal tatsächlich gestartet. Beide Versuche scheiterten beim
Download von `why-is-node-running-2.3.0.tgz` mit HTTP 503 vom internen
Paket-Proxy. Da `npm ci` nicht erfolgreich abgeschlossen wurde, konnten
`npm test`, der vollständige `vue-tsc --noEmit`-Lauf und `vite build` in dieser
Arbeitsumgebung nicht seriös ausgeführt werden.

Diese Prüfungen werden ausdrücklich **nicht als bestanden** gewertet.

### Backend: Ruff, mypy und Pytest

Die Befehle wurden aufgerufen. `ruff` und `mypy` sind in der Arbeitsumgebung
nicht installiert. Pytest konnte wegen der fehlenden Abhängigkeit `sqlmodel`
nicht bis zur Testsammlung gelangen.

Der anschließende tatsächliche Installationsversuch mit
`python -m pip install -r requirements-dev.txt` scheiterte am internen
Paketindex, der keine passende FastAPI-Version für `fastapi>=0.116,<0.117`
bereitstellte.

Die vollständigen Backendtests werden daher ausdrücklich **nicht als bestanden**
gewertet.

### Docker

`docker compose build --no-cache` wurde aufgerufen und scheiterte unmittelbar,
weil Docker in der Arbeitsumgebung nicht installiert ist. Image-Build,
Containerstart, Healthcheck, Logprüfung und praktische Browserprüfung konnten
hier nicht erfolgen und werden **nicht als bestanden** gewertet.

## 4. Verbindliche Zielsystemprüfung

In einer Umgebung mit erreichbaren npm-/Python-Paketquellen und Docker:

```bash
cd frontend
npm ci
npm test
npm run build

cd ../backend
python -m pip install -r requirements-dev.txt
ruff check app tests
mypy app
python -m pytest -q

cd ..
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Danach praktisch prüfen:

1. vorhandene Wiki-Seiten öffnen und bearbeiten;
2. **Wiki → Handbuch & Glossar** öffnen;
3. nach `Sammelschiene`, `Phasenschiene`, `FI`, `N-Schiene`, `VLAN`, `DHCP`,
   `Asset` und `Zählerstand` suchen;
4. Kategorienfilter, A–Z-Sprungmarken und interne Anker testen;
5. Desktop- und Smartphone-Darstellung prüfen;
6. bei Schutzgerät und normalem DIN-Asset **Asset bearbeiten** öffnen,
   speichern und die aktualisierten Daten in der Verteilung kontrollieren;
7. bei einer passiven Schrankkomponente kontrollieren, dass kein Asset-Button
   angezeigt wird;
8. Healthcheck und Logs auf Exceptions prüfen.

## 5. Bewertung

Der Quellstand, die statischen Inhalte, Versionsquellen und Releaseverträge sind
lokal geprüft. Das Release ist für die Zielsystemprüfung vorbereitet. Wegen der
beschriebenen Infrastrukturblockaden ist es kein vollständig durch npm, Pytest
und Docker verifiziertes Release; dieser Reststatus wird bewusst nicht
verschleiert.
## 1.4.2 – 2026-07-25

### Changelog

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

### Release Notes

DocOfHome 1.4.2 vereinfacht die Info-Seite für die geplante öffentliche
Veröffentlichung des Projekts.

## Info-Seite und Projektlinks

- Das konfigurierbare Impressum wurde vollständig aus Oberfläche und API
  entfernt.
- Projekt-, Repository-, Release- und Issue-Verweise werden nicht mehr pro
  Installation gepflegt. Sie liegen zentral im Quellcode und bleiben verborgen,
  solange das öffentliche GitHub-Repository noch nicht eingetragen ist.
- Die Lizenzinformation wird fest aus dem Projektstand angezeigt.

## Direkt aktives Feedback

Das Feedbackformular ist ohne zusätzliche Integration direkt aktiv. Das Backend
erzeugt pro Einsendung ein begrenztes ZIP mit:

- `feedback.md` für die lesbare Nachricht;
- `metadata.json` für strukturierte Angaben;
- `README.txt` mit dem übertragenen Umfang.

Das ZIP wird serverseitig an den fest hinterlegten öffentlichen Nextcloud File Drop übertragen. Datenbank, Integrationskonfiguration, Passwörter und Tokens
werden nicht aufgenommen. Browserkennung, Route, Fenstergröße und App-Version
werden weiterhin nur nach ausdrücklicher Zustimmung ergänzt.

## Datenmodell

Migration `0036_remove_configurable_about_fields` entfernt die mit 1.4.1
angelegten Projekt-, Impressums- und Feedback-Konfigurationsfelder. Gebäude-,
Asset-, Elektro-, Verbrauchs- und Integrationsdaten bleiben unverändert.

## Buildkorrekturen der Releasepakete

- `r2` stellt den versehentlich veränderten transitiven npm-Eintrag `rfdc`
  wieder auf die veröffentlichte Version `1.4.1` zurück.
- `r3` stellt die weiterhin benötigten Integrationsmetadaten und die allgemeine
  Pflichtfeldregel in `SettingsPage.vue` wieder her. Diese Hilfen werden von den
  unveränderten Home-Assistant-, Immich-, Nextcloud- und FRITZ!Box-Karten
  verwendet und waren beim Entfernen der pflegbaren About-Felder versehentlich
  mit entfernt worden.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.4.2.md

Stand: 25. Juli 2026  
Ausgangsbasis: DocOfHome 1.4.1  
Zielversion: DocOfHome 1.4.2  
Alembic-Head: `0036`

## 1. Umgesetzter Umfang

- Impressum aus Info-Seite, Settings-Oberfläche, Settings-API und Datenmodell entfernt;
- Projekt- und spätere GitHub-Verweise in eine zentrale Quellcodedatei verschoben;
- Feedback ohne private Nextcloud-Integration direkt aktiviert;
- festes öffentliches Nextcloud-File-Drop-Ziel ausschließlich im Backend;
- Feedbackpaket als ZIP mit `feedback.md`, `metadata.json` und `README.txt`;
- Größenlimit, serverseitiger Zufallsname und bestehendes Rate-Limit;
- technische Angaben weiterhin nur nach ausdrücklicher Zustimmung;
- Migration `0036_remove_configurable_about_fields`.

## 2. Tatsächlich erfolgreich ausgeführte Prüfungen

- Versionsabgleich von `VERSION`, Backend, Frontend und Lockdatei;
- Python-Compile-Prüfung für Backend, Migrationen, Tests und Scripts;
- statische Releaseverträge bis 1.4.2;
- isolierter Upgrade-/Downgrade-/Upgrade-Test der Migration `0036`;
- Quellprüfung, dass Info- und Einstellungsseite kein Impressum und keine
  pflegbaren About-Felder mehr enthalten;
- Unit-Testvertrag für Ableitung des öffentlichen WebDAV-Endpunkts und die
  erforderlichen Upload-Header;
- Unit-Testvertrag für ZIP-Inhalt, Größenbegrenzung und Zustimmung zu
  technischen Angaben;
- Release-ZIP entpackt und alle Manifestdateien anhand von Pfad, Größe und
  SHA-256 gegengeprüft.

## 3. Nicht vollständig ausführbare Prüfungen

### Frontend

Ein vollständiger `npm ci`, Vitest-, `vue-tsc`- und Vite-Lauf kann nur als
bestanden dokumentiert werden, wenn die Paketquellen in der Arbeitsumgebung
erreichbar sind. Andernfalls bleibt der Docker-Build auf dem Zielsystem das
verbindliche Qualitätsgate.

### Backend

Der vollständige Pytest-, Ruff- und mypy-Lauf hängt von den installierten
Entwicklungsabhängigkeiten ab. Ausgeführte Teilprüfungen werden nicht als Ersatz
für den vollständigen Lauf dargestellt.

### Öffentlicher File Drop

Die Arbeitsumgebung konnte `hal.scott91.de` nicht per DNS erreichen. Ein realer
Testupload in den bereitgestellten Ordner war daher nicht möglich. Die
Implementierung folgt dem öffentlichen Nextcloud-WebDAV-Endpunkt und setzt den
für schreibende Anfragen vorgesehenen Header `X-Requested-With`.

### Docker

Steht Docker in der Arbeitsumgebung nicht zur Verfügung, müssen Image-Build,
Containerstart, Migration, Healthcheck und praktischer Upload auf dem NAS
geprüft werden.

## 4. Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach eine Feedback-Testnachricht senden und prüfen, ob ein ZIP im öffentlichen
File Drop erscheint. Zusätzlich sicherstellen, dass die Info-Seite kein
Impressum und die Einstellungen keine Projekt-/Feedbackfelder mehr anzeigen.
## 5. Buildkorrektur r2

Beim ersten 1.4.2-Paket wurde die Projektversion versehentlich auch auf den
transitiven npm-Eintrag `rfdc` angewendet. Dadurch verwies die Lockdatei auf die
nicht veröffentlichte Version `rfdc@1.4.2`. Das korrigierte r2-Paket stellt die
ursprüngliche Abhängigkeit `rfdc@1.4.1` inklusive Download-URL wieder her.

Zusätzlich prüft `scripts/check-release-1.4.2.py` diesen Lockdatei-Eintrag, damit
dieser Fehler bei einer erneuten Paketierung erkannt wird. Der vollständige
`npm ci`-Lauf konnte in der Arbeitsumgebung wegen HTTP-503-Antworten des internen
Paket-Gateways nicht abgeschlossen werden.

## 6. Buildkorrektur r3

Der NAS-Build des r2-Pakets erreichte `vue-tsc`, meldete in
`SettingsPage.vue` jedoch fehlende Eigenschaften `requiredRule` und
`integrationMeta`. Beim Entfernen der konfigurierbaren About-, Impressums- und
Feedbackabschnitte waren diese weiterhin von den unveränderten
Integrationskarten verwendeten Hilfen versehentlich ebenfalls gelöscht worden.

Für r3 wurden die Definitionen aus dem zuvor vorhandenen, funktionalen
Einstellungsstand unverändert wiederhergestellt. Zusätzlich prüfen nun sowohl
`frontend/src/pages/aboutPage.test.ts` als auch
`scripts/check-release-1.4.2.py`, dass beide Definitionen vorhanden bleiben.

Tatsächlich ausgeführt wurden für r3:

- `python scripts/check-version.py`;
- `python scripts/check-release-1.4.2.py`;
- `python -m compileall -q backend/app backend/migrations scripts`;
- Vergleich der Einstellungsseite mit 1.4.1, wobei nur die bewusst entfernten
  About-/Impressums-/Feedbackbereiche und deren nun unbenutzte Hilfen fehlen;
- erneute Manifestprüfung des entpackten Releasepakets.

Ein vollständiger lokaler `npm ci`-/`vue-tsc`-/Vite-Lauf konnte in dieser
Arbeitsumgebung nicht abgeschlossen werden, weil die Paketinstallation nicht
vollständig durchlief. Der Docker-Build auf dem Zielsystem bleibt deshalb das
abschließende Qualitätsgate. Der konkret gemeldete TS2339-Ursprung ist im
r3-Quellstand beseitigt.
## 1.4.1 – 2026-07-25

### Changelog

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

### Release Notes

DocOfHome 1.4.1 ergänzt die vorbereitete Info-Seite und vereinfacht die mobile
Zählerstandserfassung direkt vom Dashboard.

## Info-Seite

Unter **Mehr → Über DocOfHome** stehen nun vier klar getrennte Bereiche zur
Verfügung:

- **Projekt** mit Zweck, lokaler Datenhaltung und optionalen Projektverweisen;
- **Versionen & Changelog** aus den mitgelieferten Release Notes;
- **Feedback** als optional aktivierbares Formular;
- **Impressum**, sobald mindestens ein konfiguriertes Feld vorhanden ist.

Die installierte Version wird aus derselben zentralen Versionsquelle wie das
Backend gelesen. Release Notes werden serverseitig geladen und im Frontend ohne
ausführbares HTML dargestellt.

## Konfiguration

In den Einstellungen können optional gepflegt werden:

- Projektwebseite, Repository-, Release- und Fehler-/Feedback-URL;
- Lizenzhinweis;
- Betreiber, Anschrift, Kontakt, verantwortliche Person, Register- und
  Umsatzsteuerangaben sowie freier Impressumstext;
- Aktivierung des Feedbackformulars und ein fester Nextcloud-Zielordner.

Leere Angaben erscheinen nicht auf der Info-Seite. Das Standard-Release enthält
keine persönlichen Impressumsdaten.

## Feedback über Nextcloud

Feedback ist standardmäßig deaktiviert. Nach Aktivierung wird es ausschließlich
über das Backend und die vorhandene Nextcloud-Integration als UTF-8-Markdown-Datei
hochgeladen. Der Browser erhält keine WebDAV-Zugangsdaten.

Technische Angaben werden nur nach sichtbarer Zustimmung übertragen. Angezeigt
und übertragen werden dann ausschließlich App-Version, betroffene Route,
Browserkennung und Fenstergröße. Dateinamen werden serverseitig aus Zeitstempel
und Zufallsanteil erzeugt. Größenlimits, feste Kategorien und ein einfaches
Rate-Limit begrenzen die Übertragung.

## Dashboard und mobile Ablesung

- Die bisherige Versionskachel wurde vom Dashboard entfernt.
- Ein gut sichtbarer Button **Zählerstände erfassen** öffnet direkt den
  Ablesedialog.
- Auf kleinen Bildschirmen nimmt der Button die volle Breite ein.
- Bestehende gespeicherte Dashboard-Layouts werden automatisch von der alten
  Systemkachel bereinigt.

## Migration

Alembic `0035_about_page_and_feedback` ergänzt ausschließlich optionale
Konfigurationsfelder. Bestehende Gebäude-, Asset-, Elektro-, Verbrauchs- und
Integrationsdaten bleiben unverändert.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.4.1.md

Stand: 25. Juli 2026  
Ausgangsbasis: DocOfHome 1.4.0  
Zielversion: DocOfHome 1.4.1  
Alembic-Head: `0035`

## 1. Umgesetzter Umfang

- zentrale Seite **Mehr → Über DocOfHome**;
- Projektbeschreibung und Hinweis auf lokale Datenhoheit;
- installierte Version aus der zentralen Backend-Versionsquelle;
- aus den ausgelieferten `RELEASE_NOTES_*.md`-Dateien geladene
  Versionshistorie;
- sichere, bewusst begrenzte Markdown-Darstellung ohne `v-html`;
- optionale Projekt-, Repository-, Release- und Issue-Verweise;
- optionaler Lizenzhinweis;
- konfigurierbares, im Standardzustand leeres Impressum;
- standardmäßig deaktiviertes Feedbackformular;
- ausdrückliche Zustimmung vor Übertragung technischer Metadaten;
- serverseitiger Feedback-Upload in einen validierten Nextcloud-Zielordner,
  ohne WebDAV-Zugangsdaten im Browser;
- serverseitig erzeugte Dateinamen, Größenlimits, Kategorien und einfaches
  Rate-Limit;
- Versionskachel vom Dashboard entfernt;
- direkter Dashboard-Button **Zählerstände erfassen**;
- automatische Bereinigung alter Dashboard-Layouts unter Erhalt von
  Reihenfolge und Sichtbarkeit der übrigen Kacheln;
- Migration `0035_about_page_and_feedback`.

## 2. Tatsächlich erfolgreich ausgeführte Prüfungen

### Quellstand und Versionen

- `python scripts/check-version.py`;
- statische Releaseverträge für 1.2.4, 1.3.0, 1.3.1, 1.3.2, 1.4.0 und 1.4.1;
- Versionsabgleich von `VERSION`, Backend, Frontend und Lockdatei;
- Python-Zeilenlängenprüfung der für 1.4.1 geänderten Dateien.

### Python und Datenverträge

- `python -m compileall -q backend/app backend/migrations backend/tests scripts`;
- Pydantic-Prüfung der Projekt-, Impressums- und Feedbackkonfiguration;
- Ablehnung leerer beziehungsweise nur aus Leerzeichen bestehender
  Pflichtangaben;
- Prüfung des validierten Nextcloud-Zielordners;
- Prüfung, dass technische Metadaten nur nach ausdrücklicher Zustimmung
  akzeptiert werden.

### Migrationen

Die eigenständigen Migrationsprüfungen für `0030` bis `0035` wurden ausgeführt.
Für Migration `0035` wurden Upgrade, Downgrade und erneutes Upgrade auf einer
repräsentativen SQLite-Ausgangsdatenbank erfolgreich geprüft. Dabei wurden die
neuen optionalen Projekt-, Impressums- und Feedbackfelder angelegt und beim
Downgrade wieder entfernt.

### Frontend-Quellstruktur

- TypeScript-Syntax aller `.ts`-Dateien und der TypeScript-Scriptblöcke aller
  Vue-Komponenten mit dem lokal vorhandenen TypeScript-Parser;
- strukturelle Prüfung der geänderten Vue-Templates auf ausgeglichene Tags;
- statische Regressionstests für Info-Seite, sichere Markdown-Ausgabe und
  direkten Zählerstandseinstieg wurden in den Quellstand aufgenommen.

### Releasepaket

Nach der finalen Paketierung wurde das ZIP in einen neuen Ordner entpackt. Alle
Manifestdateien wurden anhand von relativem Pfad, Dateigröße und SHA-256 erneut
geprüft. Die statischen Versions-, Release- und Migrationsprüfungen wurden aus
dem entpackten Releasebestand erneut ausgeführt.

## 3. Aufgenommene Regressionstests

Neu beziehungsweise erweitert wurden Tests für:

- zentrale Version, Release-Historie und leeres Impressum;
- explizite Zustimmung für technische Feedbackinformationen;
- sichere Feedbackdatei und serverseitig erzeugten Dateinamen;
- standardmäßig deaktiviertes Feedback;
- Upgrade und Downgrade der Migration `0035`;
- Entfernen der historischen Dashboard-Versionskachel ohne Verlust der
  gespeicherten Kachelreihenfolge;
- Info-API und minimierte Feedbackdaten;
- Info-Seite ohne ausführbares HTML;
- direkten Aufruf des Zählerstandsdialogs vom Dashboard.

## 4. Nicht vollständig ausführbare Prüfungen

### Frontend

`npm ci` konnte in der Arbeitsumgebung wegen nicht erreichbarer Paketquellen
nicht abgeschlossen werden. Deshalb werden Vitest, `vue-tsc --noEmit`, die
MDI-Prüfung und der vollständige Vite-Build nicht als bestanden behauptet. Die
Syntax- und Strukturprüfungen ersetzen keinen vollständigen Frontend-Build.

### Backend

Die vollständigen Entwicklungsabhängigkeiten, insbesondere `sqlmodel`, Ruff und
mypy, waren in der Arbeitsumgebung nicht verfügbar und konnten wegen fehlender
Namensauflösung nicht nachinstalliert werden. Deshalb werden der vollständige
Pytest-, Ruff- und mypy-Lauf nicht als bestanden behauptet. Python-Syntax,
Pydantic-Verträge und die eigenständigen Alembic-/SQLAlchemy-Migrationsprüfungen
wurden tatsächlich ausgeführt.

### Docker

Docker oder Podman steht in der Arbeitsumgebung nicht zur Verfügung. Image-Build,
Containerstart, Healthcheck und praktische Browserprüfung müssen auf dem
Zielsystem erfolgen.

## 5. Empfohlene Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach prüfen:

1. Alembic aktualisiert ohne Fehler auf Head `0035`.
2. **Mehr → Über DocOfHome** öffnet ohne Fehler.
3. Die Seite zeigt Version `1.4.1` und die Release-Historie.
4. Leere Projektlinks und ein leeres Impressum bleiben ausgeblendet.
5. Nach Pflege in den Einstellungen erscheinen nur die gesetzten Angaben.
6. Feedback bleibt standardmäßig unsichtbar beziehungsweise deaktiviert.
7. Bei aktivierter Nextcloud-Integration wird Feedback als Markdown-Datei im
   konfigurierten Ordner gespeichert.
8. Ohne Zustimmung werden keine technischen Metadaten übertragen.
9. Die Versionskachel ist vom Dashboard entfernt.
10. **Zählerstände erfassen** öffnet auf dem Smartphone direkt den
    Ablesedialog.
11. Ein zuvor individuell sortiertes Dashboard behält nach der Bereinigung die
    Reihenfolge und Sichtbarkeit seiner verbleibenden Kacheln.
12. Bestehende Elektro-, Verbrauchs-, Asset- und Integrationsdaten bleiben
    unverändert vorhanden.

## 6. Bewertung

Der vereinbarte Funktionsumfang ist im Quellstand umgesetzt. Versionen,
Migrationen, Quellsyntax, Datenvalidierung und Release-Roundtrip wurden geprüft.
Die produktive Freigabe bleibt vom vollständigen npm-/Backend-/Docker-Lauf und
der praktischen Prüfung auf dem NAS abhängig.
## 1.4.0 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.4.0 macht die Schrankaufteilung für eine private Hausdokumentation
übersichtlicher und ergänzt eine einfache, nachvollziehbare Logik für
Sammelschienen, FI/RCD-Gruppen und Neutralleiterschienen.

## Sammelschienen

Eine Sammelschiene wird als passive Schrankkomponente angelegt. Zusätzlich zu
Reihe und Startposition werden die überspannten TE, die vorhandenen Phasen, eine
Startphase und optional der speisende FI/RCD hinterlegt.

Beispiel mit Startphase L1:

```text
TE 1  L1
TE 2  L2
TE 3  L3
TE 4  L1
TE 5  L2
TE 6  L3
```

Sammelschienen liegen als Überlagerung unter den Schutzgeräten und blockieren
deren TE-Platz nicht. Andere Bauteile kollidieren weiterhin wie bisher.

## FI- und Neutralleiter-Zuordnung

- Eine Sammelschiene kann einem FI/RCD zugeordnet werden.
- Eine N-Schiene kann demselben FI/RCD zugeordnet werden.
- Schutzgeräte unter der Sammelschiene erhalten daraus automatisch die wirksame
  FI-Gruppe, die passende N-Schiene und ihre Phase.
- Manuelle Zuordnungen bleiben möglich.
- Abweichungen werden als verständliche Warnung angezeigt, nicht als unnötige
  harte Sperre.

Die automatisch ermittelten Werte werden nicht ungefragt als manuelle Werte in
das Schutzgerät geschrieben. Verschieben per Drag-and-drop kann die wirksame
Gruppe daher korrekt neu berechnen.

## Optimierte Schrankansicht

- Belegte und freie TE, nicht platzierte Geräte und Hinweise auf einen Blick;
- kompakte und erweiterte Darstellung;
- Phasen-, FI- und N-Schienen-Anzeige direkt am Schutzgerät;
- Sammelschiene als eigene Leiste mit Phasenfolge;
- Detailpanel für Schutzgerät, Schrankkomponente und DIN-Asset;
- separate Ablage für noch nicht platzierte Schutzgeräte und DIN-Assets;
- Drag-and-drop auf dem Desktop und weiterhin dialogbasierte Positionierung auf
  kleinen Bildschirmen.

## Migration

Alembic `0034_home_electrical_groups` ergänzt optionale Felder. Bestehende
Verbindungen, Geräte, Platzierungen und Schrankkomponenten werden nicht gelöscht
oder automatisch umgedeutet.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.4.0.md

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.3.2  
Zielversion: DocOfHome 1.4.0  
Alembic-Head: `0034`

## 1. Umgesetzter Umfang

- Sammelschienen als passive Schrankkomponenten mit TE-Spanne, auswählbaren
  Außenleitern und Startphase;
- wiederholte Phasenfolge anhand der Position, beispielsweise
  `L1 – L2 – L3 – L1`;
- Zuordnung einer Sammelschiene zu einem FI/RCD;
- Zuordnung einer N-Schiene zu einem FI/RCD;
- automatische Ermittlung der wirksamen FI-Gruppe, N-Schiene und Phase eines
  Schutzgeräts unter einer Sammelschiene;
- manuelle Zuordnung mit Warnung bei abweichender oder unvollständiger
  Dokumentation;
- Sammelschiene als nicht platzverbrauchendes Overlay unter Schutzgeräten;
- optimierte Verteilungsansicht mit TE-Belegung, Kompakt-/Erweitert-Modus,
  Gruppeninformationen, Warnungen und Detailpanel;
- neue Migration `0034_home_electrical_groups`.

Der Umfang bleibt bewusst auf eine verständliche private Hausdokumentation
begrenzt. Einzelne Klemmen, Zähne oder Neutralleiteranschlüsse werden nicht
verwaltet.

## 2. Erfolgreich ausgeführte Prüfungen

Folgende Prüfungen wurden in der Arbeitsumgebung tatsächlich ausgeführt:

- Python-Syntaxprüfung für Backend, Migrationen, Tests und Skripte mit
  `python -m compileall`;
- Versionskonsistenz über `VERSION`, Backend, Frontend und Lockdatei;
- statische Releaseverträge für die Releases 1.2.4 bis 1.4.0;
- isolierte Migrationsprüfungen für `0030`, `0031`, `0032`, `0033` und `0034`;
- Migration `0034`: Upgrade, Downgrade und erneutes Upgrade auf einer
  repräsentativen SQLite-Datenbank;
- Pydantic-Validierung für eine dreiphasige Sammelschiene und eine reine
  N-Schiene;
- TypeScript-Syntaxprüfung der geänderten Frontend-Dateien über
  `typescript.transpileModule`;
- strukturelle Prüfung des Vue-Templates auf ausgeglichene Tags;
- ZIP-Roundtrip mit Größen- und SHA-256-Prüfung sämtlicher Manifestdateien
  nach der finalen Paketierung.

Zusätzlich wurden Regressionstests in den Quellstand aufgenommen für:

- die wiederholte Phasenfolge einer Sammelschiene;
- eine vom FI gespeiste Sammelschiene mit automatisch zugeordneter N-Schiene;
- Upgrade und Downgrade der Migration `0034`.

## 3. Nicht vollständig ausführbare Prüfungen

### Frontend

`npm ci` konnte in der Arbeitsumgebung nicht abgeschlossen werden, weil die
Paketquelle nicht zuverlässig erreichbar war. Deshalb werden Vitest,
`vue-tsc --noEmit` und der vollständige Vite-Build nicht als bestanden
behauptet. Die geänderten TypeScript-Quellen wurden syntaktisch geprüft, dies
ersetzt den vollständigen Frontend-Build jedoch nicht.

### Backend

Das erforderliche Paket `sqlmodel` war in der Arbeitsumgebung nicht installiert
und konnte von der verfügbaren Paketquelle nicht bezogen werden. Deshalb wurden
der vollständige Pytest-, Ruff- und mypy-Lauf nicht als bestanden gewertet.
Python-Syntax, Pydantic-Schemata und die eigenständige Alembic-/SQLAlchemy-
Migrationsprüfung wurden tatsächlich ausgeführt.

### Docker

Docker oder Podman steht in der Arbeitsumgebung nicht zur Verfügung. Image-Build,
Containerstart, Healthcheck und praktische Browserprüfung müssen auf dem
Zielsystem erfolgen.

## 4. Empfohlene Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach prüfen:

1. Alembic aktualisiert ohne Fehler auf Head `0034`.
2. Eine vorhandene Verteilung öffnet weiterhin ohne Datenverlust.
3. Ein FI/RCD lässt sich einer Sammelschiene und einer N-Schiene zuordnen.
4. Die Sammelschiene kann dieselben TE wie die zugehörigen Sicherungen
   überlagern.
5. Bei Startphase `L1` werden die Gerätepositionen wiederholend als
   `L1, L2, L3, L1 ...` angezeigt.
6. Beim Verschieben einer Sicherung wird die wirksame Phase neu berechnet.
7. FI und N-Schiene erscheinen am Schutzgerät und im Detailpanel.
8. Eine N-Schiene eines anderen FI erzeugt eine sichtbare Warnung.
9. Schutzgeräte und normale DIN-Assets lassen sich per Drag-and-drop sowie über
   den Positionierungsdialog verschieben.
10. Bestehende Mehrfacheinspeisungen, Verkabelungen und Verbrauchsdaten bleiben
    erhalten.

## 5. Bewertung

Der Sprintumfang ist im Quellstand umgesetzt und die neue Datenmigration wurde
isoliert erfolgreich geprüft. Die endgültige produktive Freigabe bleibt vom
vollständigen Frontend-/Backend-/Docker-Lauf und der praktischen Prüfung auf dem
Zielsystem abhängig.
## 1.3.2 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.3.2 korrigiert Mehrfacheinspeisungen an Phasenverteilerblöcken auf
bereits bestehenden Installationen.

## Ursache

Die ursprüngliche elektrische Topologie besaß einen eindeutigen Index auf
`target_kind` und `target_id`. Damit war je Ziel nur eine aktive Quelle möglich.
Migration `0027` entfernte diese Beschränkung in neuen Datenbanken. Auf Systemen,
die `0027` bereits mit einem älteren Stand ausgeführt hatten, wurde eine später
korrigierte historische Migration jedoch nicht erneut ausgeführt. Der alte
Index blieb deshalb erhalten, obwohl Anwendung und Tests Mehrfacheinspeisungen
unterstützten.

## Korrektur

Migration `0033_remove_legacy_single_target_topology_index` prüft die reale
Datenbank und entfernt den Index
`uq_electrical_connections_active_target`, falls er noch vorhanden ist.

Danach sind beispielsweise folgende Verbindungen gleichzeitig möglich:

```text
Zähler / Sunny Home Manager -> Phasenverteilerblock L1
PV-Wechselrichter           -> Phasenverteilerblock L1
Phasenverteilerblock L1     -> Unterverteilung / Sammelschiene
```

Die Eindeutigkeit des vollständigen Verbindungspaars bleibt erhalten. Dieselbe
Quelle kann also nicht versehentlich zweimal mit demselben Ziel verbunden
werden.

## Phasenlogik

Die bestehende Leiterprüfung bleibt aktiv:

- eine Komponente akzeptiert nur konfigurierte Leiter;
- ein Ausgang für L2 ist nur zulässig, wenn L2 mindestens einmal eingespeist ist;
- L1 wird nicht automatisch zu L2 oder L3 umgedeutet;
- mehrere Quellen dürfen denselben Leiter einspeisen.

## Update

Vor dem Update den persistenten Datenordner sichern. Beim Containerstart führt
Alembic Migration `0033` automatisch aus. Danach die zweite Einspeisung erneut
anlegen.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.3.2.md

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.3.1-r2  
Zielversion: DocOfHome 1.3.2  
Alembic-Head: `0033`

## 1. Fehlerursache

Die Anwendung und die aktuellen Modelle erlaubten bereits mehrere eingehende
Verbindungen an einem Phasenverteilerblock. Auf bestehenden Installationen war
jedoch teilweise weiterhin der historische SQLite-Index
`uq_electrical_connections_active_target` vorhanden. Dieser Index erzwang trotz
Anwendungslogik genau eine aktive Quelle je Ziel.

Die Ursache lag darin, dass Migration `0027` auf der betroffenen Installation
bereits als ausgeführt markiert war. Eine nachträgliche Korrektur derselben
historischen Migrationsdatei wird von Alembic nicht erneut angewendet.

## 2. Umgesetzte Korrektur

- neue Migration `0033_remove_legacy_single_target_topology_index`;
- idempotente Prüfung, ob der historische Ziel-Unique-Index noch existiert;
- Entfernung ausschließlich dieses Indexes;
- keine Änderung oder Löschung bestehender Verbindungen;
- weiterhin eindeutige vollständige Verbindungspaare, damit dieselbe Quelle
  nicht doppelt mit demselben Ziel verbunden werden kann;
- deutsche und konkretere Datenbank-Konfliktmeldungen;
- Regressionstest für eine bereits bis `0032` migrierte Alt-Datenbank mit
  verbliebenem Ziel-Unique-Index.

## 3. Erfolgreich ausgeführte Prüfungen

- `python -m compileall -q backend/app backend/tests backend/migrations/versions scripts`
- `python scripts/check-version.py`
- `python scripts/check-branding.py`
- `python scripts/check-collected-fixes.py`
- `python scripts/check-reading-reminders.py`
- `python scripts/check-release-1.2.4.py`
- `python scripts/check-release-1.3.0.py`
- `python scripts/check-release-1.3.1.py`
- `python scripts/check-release-1.3.2.py`
- `python scripts/check-migration-0030.py`
- `python scripts/check-migration-0031.py`
- `python scripts/check-migration-0032.py`
- `python scripts/check-migration-0033.py`

Die isolierte Prüfung von Migration `0033` hat den historischen Index entfernt
und anschließend zwei unterschiedliche Quellen auf demselben
`cabinet_component`-Ziel erfolgreich gespeichert. Ein erneutes Upgrade blieb
idempotent.

## 4. Nicht vollständig ausführbare Prüfungen

### Frontend

`npm ci` konnte in der Arbeitsumgebung nicht abgeschlossen werden. Die
Paketquelle antwortete innerhalb des verfügbaren Zeitfensters nicht vollständig.
Daher wurden `vue-tsc --noEmit`, `vite build` und Vitest für diesen Stand nicht
als bestanden gewertet. An den Frontend-Quellen war für 1.3.2 keine funktionale
Änderung erforderlich.

### Backend

Das vollständige Backend-Paket `sqlmodel` war in der Umgebung nicht verfügbar
und konnte von der Paketquelle nicht installiert werden. Deshalb wurde der
komplette Pytest-Lauf nicht ausgeführt. Python-Syntax und die eigenständige
Alembic-/SQLAlchemy-Migrationsprüfung wurden tatsächlich ausgeführt.

### Docker

Docker oder Podman steht in der Arbeitsumgebung nicht zur Verfügung. Image-Build,
Containerstart, Healthcheck und praktische Browserprüfung müssen auf dem
Zielsystem erfolgen.

## 5. Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach prüfen:

1. Alembic-Head ist `0033` und es erscheint kein Migrationsfehler.
2. Eine vorhandene Einspeisung zum Phasenverteilerblock bleibt bestehen.
3. Eine zweite Quelle kann auf denselben Phasenverteilerblock gespeichert werden.
4. Beide Einspeisungen werden in der Versorgungstopologie angezeigt.
5. Eine identische Verbindung zwischen derselben Quelle und demselben Ziel wird
   weiterhin abgelehnt.
6. Phasenregeln bleiben aktiv: Ein ausschließlich mit L1 versorgter Block darf
   L2 nicht als Abgang ausgeben.

## 6. Bewertung

Die konkrete Ursache der gemeldeten Mehrfacheinspeisungsstörung ist mit einer
neuen, für Bestandsinstallationen wirksamen Migration korrigiert. Die
Paketfreigabe bleibt abhängig vom vollständigen Docker-Build und der praktischen
Prüfung auf dem Zielsystem.
## 1.3.1 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.3.1 korrigiert die DIN-Schienenansicht, erweitert die
DIN-Breitenlogik und macht Mehrfacheinspeisungen an passiven
Schrankkomponenten fachlich prüfbar. Außerdem wird der laufende
Verbrauchsmonat nur noch bis heute bewertet.

## DIN-Assets direkt auf der Hutschiene

Normale Assets mit einer wirksamen DIN-Breite – beispielsweise Smart Meter –
werden jetzt gemeinsam mit Schutzgeräten und passiven Schrankkomponenten im
TE-Raster dargestellt. Ein platzierter Smart Meter mit vier TE belegt damit
sichtbar vier zusammenhängende Modulplätze statt unterhalb der Schiene zu
erscheinen.

Auf breiten Desktop-Ansichten können Schutzgeräte und normale DIN-Assets per
Drag-and-drop innerhalb einer Reihe sowie zwischen Reihen und Gerätebereichen
verschoben werden. Die Kollisionsprüfung berücksichtigt alle drei Objektarten.
Auf Touchgeräten bleibt der Positionsdialog der verlässliche Bedienweg.

## DIN-Breite ohne Produktpflicht

Eine optionale DIN-Breite kann jetzt direkt hinterlegt werden:

1. am einzelnen Asset;
2. an einem DIN-Produkt;
3. als Standard am Asset-Typ.

Die Reihenfolge der wirksamen Breite ist **Asset vor Produkt vor Asset-Typ**.
Damit können Typen wie Sicherungsautomat, FI-Schalter, FI/LS-Schalter oder Smart
Meter eine typische TE-Breite mitbringen, ohne dass zuvor zwingend ein
Produktstammsatz angelegt werden muss. Schutzgeräte übernehmen diese Breite
automatisch in Editor, Positionsdialog und Drag-and-drop. Nur Assets mit einer
wirksamen DIN-Breite werden in der Oberfläche als neu platzierbare DIN-Geräte
angeboten. Bereits vorhandene Schutzgerätebreiten bleiben aus Gründen der
Rückwärtskompatibilität verwendbar.

## Mehrere Einspeisungen und Phasenprüfung

Ein Phasenverteilerblock oder eine andere passive Schrankkomponente kann mehrere
gleichzeitige eingehende Verbindungen besitzen. So lassen sich beispielsweise
Netz-/Zählerpfad und PV-Wechselrichter als zwei dokumentierte Einspeisungen
desselben Blocks abbilden. Die Oberfläche zeigt alle eingehenden Verbindungen
und deren gemeinsame Leiter an.

Für Schrankkomponenten gelten nun folgende Prüfungen:

- jede Verbindung führt ihre ausgewählten Leiter unverändert von Quelle zu Ziel;
- `L1` kann nicht stillschweigend als `L2` weitergeführt werden;
- eine Komponente darf nur Leiter verwenden, die in ihrer Konfiguration
  freigegeben sind;
- ausgehend dürfen nur Leiter verwendet werden, die über mindestens eine der
  aktiven Einspeisungen tatsächlich anliegen;
- das Ändern oder Löschen einer Einspeisung wird abgelehnt, wenn dadurch bereits
  dokumentierte Abgänge nicht mehr versorgt wären.

## Laufender Verbrauchsmonat

Der Zeitraum **Aktueller Monat** endet jetzt bei „heute“ statt am ersten Tag des
Folgemonats. Eine Ablesung am aktuellen Tag gilt für diesen laufenden Zeitraum
als ausreichende Endabdeckung; eine sekundengenaue Ablesung zum aktuellen
Zeitpunkt oder eine Ablesung aus der Zukunft wird nicht mehr verlangt.
Historische, abgeschlossene Zeiträume behalten ihre strenge
Vollständigkeitsprüfung.

## Datenbank

Migration `0032_asset_and_type_din_width` ergänzt optionale, validierte
`module_width`-Felder bei Asset-Typen und Assets. Bestehende Datensätze erhalten
`NULL` und werden nicht fachlich umgeschrieben.

## Build-Korrektur

Die Initialisierung des Asset-Formulars auf der Home-Assistant-Seite enthält
nun ebenfalls das mit 1.3.1 eingeführte Feld `module_width`. Dadurch ist das
Formular wieder vollständig mit dem TypeScript-Typ `AssetWrite` kompatibel und
`vue-tsc --noEmit` bricht nicht mehr mit TS2345 ab.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.3.1.md

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.3.0  
Zielversion: DocOfHome 1.3.1  
Alembic-Head: `0032`

## 1. Umgesetzter Umfang

- Darstellung normaler DIN-Assets direkt im TE-Raster;
- Drag-and-drop für Schutzgeräte und normale DIN-Assets in einfacher und
  strukturierter Reihenaufteilung;
- gemeinsame Kollisionsprüfung mit passiven Schrankkomponenten;
- optionale DIN-Breite an Asset-Typ und Asset ohne Produktpflicht;
- wirksame Breitenreihenfolge Asset, DIN-Produkt, Asset-Typ;
- automatische Übernahme dieser Breite für Sicherungen, FI/RCD und andere
  Schutzgeräte;
- mehrere eingehende Versorgungsverbindungen an einer Schrankkomponente;
- Leiterprüfung für konfigurierte und tatsächlich eingespeiste Phasen;
- Anzeige aller Einspeisungen in Topologie und Inline-Verkabelungsübersicht;
- laufender Verbrauchsmonat bis heute mit tagesbezogener Endabdeckung;
- Migration `0032`.

## 2. Erfolgreich ausgeführte Prüfungen

- `python -m compileall -q backend/app backend/tests backend/migrations/versions scripts`
- `python scripts/check-version.py`
- `python scripts/check-release-1.2.4.py`
- `python scripts/check-release-1.3.0.py`
- `python scripts/check-release-1.3.1.py`
- statische Vertragsprüfung der vollständigen `AssetWrite`-Initialisierung auf der Home-Assistant-Seite;
- `python scripts/check-migration-0030.py`
- `python scripts/check-migration-0031.py`
- `python scripts/check-migration-0032.py`
- statische TypeScript-Syntaxprüfung der geänderten `.ts`-Dateien und der
  `<script setup>`-Blöcke der geänderten Vue-Dateien mit dem lokal vorhandenen
  TypeScript-Compiler;
- Prüfung der geänderten Python-Dateien auf Zeilen über 100 Zeichen;
- Prüfung auf verbotene Cache-, Build-, Datenbank- und Secret-Dateien;
- Entpacken des finalen ZIP und Prüfung jeder Manifestposition auf Dateigröße
  und SHA-256.

Migration `0032` wurde gegen eine repräsentative SQLite-Datenbank als Upgrade,
Downgrade und erneutes Upgrade ausgeführt.

## 3. Enthaltene Regressionstests

Der Quellstand enthält Tests für:

- Breite vom Asset-Typ und direkte Überschreibung am Asset;
- Übernahme der Asset-Typbreite beim Anlegen und Platzieren eines Schutzgeräts;
- Ablehnung eines Assets ohne wirksame DIN-Breite;
- Ablehnung einer von der Stammdatenbreite abweichenden Platzierungsbreite;
- Mehrfacheinspeisung eines L1/L2/L3-Phasenverteilerblocks;
- Sperre einer Einspeisungsänderung, wenn dadurch Abgänge unversorgt wären;
- Ablehnung von L2 als Ausgang, wenn nur L1 eingespeist wird;
- Ablehnung nicht konfigurierter Leiter wie N;
- Anzeige mehrerer Einspeisungen im Frontend;
- vollständigen laufenden Monat nach einer heutigen Ablesung;
- Darstellung und Drag-and-drop normaler DIN-Assets im Reihenraster.

## 4. Nicht ausführbare Prüfungen in dieser Umgebung

### Frontend

Der auf dem Zielsystem gemeldete TypeScript-Fehler TS2345 in
`SmartHomePage.vue` wurde durch die fehlende Initialisierung von `module_width`
verursacht und im Quellstand korrigiert. Alle weiteren Stellen, die
`AssetWrite` unmittelbar erzeugen, wurden auf dieses Pflichtfeld geprüft.

Ein erneuter lokaler `npm ci --no-audit --no-fund` scheiterte jedoch weiterhin
an der konfigurierten Paketquelle mit HTTP 503 beim Paket
`why-is-node-running` 2.3.0. Deshalb konnten `npm test`, `vue-tsc --noEmit` und
`vite build` in dieser Umgebung nicht erneut vollständig ausgeführt werden.
Der korrigierte Docker-Build auf dem Zielsystem bleibt die verbindliche
Endprüfung.

### Backend

Für den vollständigen Backend-Testlauf fehlt in der Umgebung das Projektpaket
`sqlmodel`; außerdem stehen Ruff und mypy nicht zur Verfügung. Die enthaltenen
Pytest-Tests konnten deshalb nicht vollständig ausgeführt werden. Python-Syntax
und die eigenständigen Migrationsprüfungen wurden dagegen tatsächlich
abgeschlossen.

### Docker

Docker oder Podman ist nicht verfügbar. Image-Build, Containerstart,
Healthcheck und praktische Browserprüfung müssen auf dem Zielsystem erfolgen.

## 5. Verbindliche Zielsystemprüfung

```bash
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Danach mindestens prüfen:

1. Smart Meter mit 4 TE im Raster und nicht unterhalb der Schiene;
2. Drag-and-drop desselben Assets innerhalb und zwischen Reihen;
3. Kollision mit Schutzgerät oder Phasenverteilerblock;
4. Asset-Typbreite ohne Produktstammsatz;
5. zwei Einspeisungen an einem Phasenverteilerblock;
6. Ablehnung eines L1-zu-L2-Fehlers;
7. aktueller Verbrauchsmonat nach heutiger Ablesung;
8. Backend-Logs ohne Migrationsexception oder HTTP 500.

## 6. Bewertung

Der Stand ist als Release Candidate für DocOfHome 1.3.1 paketiert. Statische
Prüfungen, Migrationsprüfung und Paketintegrität sind erfolgreich. Die endgültige
Freigabe hängt vom vollständigen Frontend-/Backend-/Docker-Lauf auf dem
Zielsystem ab.
## 1.3.0 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.3.0 erweitert die elektrische Schrankdokumentation um passive,
nicht als Asset geführte Schrankkomponenten und behebt die Platzierung in
Unterverteilungen mit einfacher Reihenaufteilung.

## Neue Schrankkomponenten

In einer Haupt- oder Unterverteilung können jetzt folgende passive Komponenten
angelegt und auf einer DIN-Schiene positioniert werden:

- Phasenverteilerblock;
- Sammelschiene und Phasenschiene;
- N- und PE-Schiene;
- Reihen- und Anschlussklemme;
- Potentialverteiler;
- sonstige passive Schrankkomponente.

Jede Komponente erhält Bezeichnung, Reihe, TE-Startposition, TE-Breite und die
zugehörigen Leiter `L1`, `L2`, `L3`, `N` und/oder `PE`. Optional können
Bemessungsstrom, maximaler Leiterquerschnitt, Zahl der Abgänge, Beschreibung und
Notizen dokumentiert werden. Die Komponenten sind bewusst keine Assets.

## Verkabelung und Versorgungstopologie

Schrankkomponenten stehen als eigener Endpunkttyp `cabinet_component` in der
Elektro-Verkabelung zur Verfügung. Dadurch lässt sich beispielsweise folgender
Versorgungsweg dokumentieren:

`Netzanschluss → Vorsicherung → Zähler → Phasenverteilerblock → Unterverteilungen / PV / Sammelschiene`

Verkabelte Komponenten können erst archiviert werden, wenn ihre Verbindungen
entfernt wurden. Bestehende Asset-, Verteilungs-, Schutzgeräte- und
Stromkreis-Endpunkte bleiben unverändert.

## Reihenaufteilung und Unterverteilungen

- Schutzgeräte lassen sich auch bei Verteilungen im Modus **Einfache Reihen**
  per Drag-and-drop auf Reihe und TE-Position verschieben.
- DIN-Assets und passive Schrankkomponenten können ebenfalls in einer einfachen
  Reihenaufteilung platziert werden.
- Die Serienanlage verlangt bei einer einfachen Reihenaufteilung keinen
  DIN-Bereich mehr. Ein DIN-Bereich wird nur im Feld-/Bereichsmodus angezeigt
  und übertragen.
- Überschneidungen zwischen Schutzgeräten, DIN-Assets und Schrankkomponenten
  werden serverseitig und in der Oberfläche verhindert.

## Datenbank

Migration `0031_cabinet_components_and_rows_placements`:

- legt die Tabelle `electrical_cabinet_components` an;
- erlaubt `NULL` bei `electrical_asset_placements.area_id`, damit DIN-Assets in
  einfachen Reihen platziert werden können;
- erweitert die zulässigen Elektro-Endpunkttypen um `cabinet_component`.

Vor dem Update ist ein vollständiges Backup des persistenten `data`-Ordners zu
erstellen.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.3.0.md

Stand: 24. Juli 2026  
Ausgangsbasis: DocOfHome 1.2.4  
Zielversion: DocOfHome 1.3.0  
Alembic-Head: `0031`

## 1. Umgesetzter Umfang

- passive Schrankkomponenten als eigene, nicht als Asset geführte Objekte;
- Typen für Phasenverteilerblock, Sammel-/Phasenschiene, N-/PE-Schiene,
  Reihen-/Anschlussklemme, Potentialverteiler und sonstige Komponenten;
- Platzierung über Reihe, TE-Startposition und TE-Breite in einfachen Reihen
  sowie in strukturierten Gerätebereichen;
- Zuordnung von `L1`, `L2`, `L3`, `N` und `PE` sowie optionalen technischen
  Angaben und der Zahl der Abgänge;
- Endpunkttyp `cabinet_component` für Elektro-Verkabelung und Topologie;
- gemeinsame Kollisionsprüfung für Schutzgeräte, DIN-Assets und passive
  Schrankkomponenten;
- Drag-and-drop von Schutzgeräten in Verteilungen mit einfacher
  Reihenaufteilung;
- Serienplatzierung in einfacher Reihenaufteilung ohne DIN-Bereichspflicht;
- Migration `0031` für Datenmodell und Endpunkttypen.

## 2. Erfolgreich ausgeführte Prüfungen

### Quellstand und Versionen

- `python scripts/check-version.py`
- `python scripts/check-release-1.2.4.py`
- `python scripts/check-release-1.3.0.py`
- Versionsabgleich von `VERSION`, Backend und Frontend: erfolgreich
- Prüfung auf Python-Zeilen über 100 Zeichen in den geänderten Dateien:
  ohne Treffer

### Python- und Frontend-Quellsyntax

- `python -m compileall -q backend/app backend/migrations scripts`
- zusätzliche `py_compile`-Prüfung der zentralen Layoutlogik
- TypeScript-Syntaxprüfung aller `.ts`-Dateien und aller Scriptblöcke der
  Vue-Dateien mit dem lokal vorhandenen TypeScript-Parser
- HTML-Fragmentprüfung der Templates von
  `ElectricalDistributionLayoutPage.vue` und `AssetDuplicateDialog.vue`

Diese Prüfungen bestätigen die syntaktische Lesbarkeit des Quellcodes. Sie
ersetzen nicht den vollständigen Lauf von `vue-tsc`, Vite oder Pytest.

### Migrationen

- `python scripts/check-migration-0030.py`
- `python scripts/check-migration-0031.py`
- Upgrade, Downgrade und erneutes Upgrade von Migration `0031` gegen eine
  repräsentative SQLite-Ausgangsdatenbank mit SQLAlchemy/Alembic
- dabei geprüft:
  - Tabelle `electrical_cabinet_components` wird erstellt und entfernt;
  - `electrical_asset_placements.area_id` wird nullable und beim Downgrade
    wieder verpflichtend;
  - `cabinet_component` wird in den Check-Constraints der Elektroverbindungen
    zugelassen und beim Downgrade wieder entfernt.

### Releasepaket

Nach Erstellung des finalen Pakets wurden zusätzlich ausgeführt:

- Entpacken des ZIP in einen neuen Prüfpfad;
- Prüfung jeder Manifestposition auf Pfad, Dateigröße und SHA-256;
- Prüfung auf nicht erlaubte Cache-, Build-, Datenbank- und Secret-Dateien;
- erneuter Lauf der statischen Versions-, Release-, Migrations- und
  Syntaxprüfungen aus dem entpackten Bestand.

## 3. Enthaltene Regressionstests

Der Quellstand enthält neue beziehungsweise angepasste Tests für:

- Schutzgeräteplatzierung im Reihenmodus mit `area_id = null`;
- passive Schrankkomponenten und ihre Leiterzuordnung;
- gemeinsame TE-Kollisionsprüfung;
- Bereitstellung von Schrankkomponenten als Verkabelungsendpunkte;
- Sperre beim Archivieren einer noch verkabelten Schrankkomponente;
- Serienplatzierung ohne DIN-Bereich im Reihenmodus;
- Frontend-Verträge für Reihen-Drag-and-drop und Schrankkomponenten.

Die Tests sind im Release enthalten, konnten in dieser Umgebung jedoch nicht
mit dem vollständigen Projekt-Dependency-Set ausgeführt werden.

## 4. Nicht ausführbare Prüfungen

### Frontend-Build und Vitest

`npm ci`, `npm test`, `vue-tsc --noEmit` und `vite build` konnten nicht
vollständig ausgeführt werden. Die konfigurierte npm-Paketquelle antwortete bei
der Abhängigkeitsabfrage mit:

```text
503 Service Temporarily Unavailable
```

Dadurch standen die lokalen Projektpakete einschließlich `vue-tsc`, Vite und
Vitest nicht zur Verfügung. Es wird deshalb ausdrücklich **nicht** behauptet,
dass der vollständige Frontend-Build in dieser Umgebung bestanden hat.

### Backend-Pytest, Ruff und mypy

Die Umgebung enthält SQLAlchemy, Alembic und Pytest, aber nicht die für den
vollständigen Anwendungslauf erforderlichen Pakete `sqlmodel`, `ruff` und
`mypy`. Deshalb konnten weder der komplette Backend-Testlauf noch Ruff und mypy
ausgeführt werden. Die Migration wurde unabhängig davon mit einer
repräsentativen SQLite-Struktur geprüft.

### Docker

In der Releaseumgebung ist weder Docker noch Podman verfügbar. Ein
`docker compose build`, Containerstart, Healthcheck und die praktische Prüfung
in der gebauten Anwendung waren daher nicht möglich.

## 5. Verbindliche Zielsystemprüfung vor produktivem Einsatz

Im Zielsystem sind mindestens auszuführen:

```bash
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Zusätzlich praktisch prüfen:

1. Unterverteilung im Modus **Einfache Reihen** öffnen und ein Schutzgerät per
   Drag-and-drop auf eine freie TE-Position verschieben.
2. Eine Serie von Sicherungen in einer Reihenverteilung anlegen; es darf kein
   DIN-Bereich verlangt werden.
3. Einen **Phasenverteilerblock L1/L2/L3** als Schrankkomponente anlegen und auf
   der DIN-Schiene positionieren.
4. Verbindungen wie
   `Netzanschluss → Vorsicherung → Zähler → Phasenverteilerblock → Unterverteilung`
   anlegen.
5. Weitere Abgänge vom Phasenverteilerblock zu Unterverteilungen, PV-Anlage und
   Sammelschiene erfassen.
6. Überschneidende TE-Platzierungen müssen kontrolliert abgewiesen werden.
7. Eine verkabelte Schrankkomponente darf erst nach Entfernen ihrer Verbindungen
   archiviert werden.
8. Backend-Logs auf Migration-, Validierungs- oder HTTP-500-Fehler prüfen.

## 6. Bewertung

Der Quellstand ist als **Release Candidate für DocOfHome 1.3.0** paketiert. Die
statischen Prüfungen, die repräsentative Migrationsprüfung und die
Manifestprüfung sind erfolgreich. Die endgültige Freigabe hängt noch vom
vollständigen npm-/Vite-/Vitest-Lauf, Backend-Testlauf und Docker-Praxistest im
Zielsystem ab.
## 1.2.4 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.2.4 ist ein Patch-Release für vier gemeldete Fehler in der
Produktbildsuche, der elektrischen Schrankaufteilung, dem Netzwerkmodul und der
Benachrichtigungsdarstellung.

## Online-Produktbilder

Die serverseitige Wikimedia-Suche bleibt der bevorzugte Weg. Kann der
DocOfHome-Container Wikimedia wegen DNS, TLS, Proxy, Firewall oder eines
externen Ausfalls nicht erreichen, versucht das Frontend die offizielle
Wikimedia-API direkt aus dem Browser mit CORS-Unterstützung.

- nur `commons.wikimedia.org` und `upload.wikimedia.org` werden akzeptiert;
- frühere Suchläufe werden bei einem neuen Suchbegriff abgebrochen;
- Suche, Download und Upload besitzen Zeitlimits;
- erst der ausdrücklich ausgewählte Treffer wird übernommen;
- der Browser lädt den Treffer bei Bedarf herunter und überträgt ihn über den
  bestehenden Upload-Endpunkt zur lokalen Speicherung in DocOfHome;
- Fehlermeldungen unterscheiden Backend-Ausfall, externe Nichterreichbarkeit,
  leere Trefferlisten und fehlgeschlagene Bilddownloads.

Upload, Immich-Auswahl und manuelle URL bleiben erhalten.

## Schrankaufteilung von Unterverteilungen

Die Schrankaufteilung ist nun bei Haupt- und Unterverteilungen aufrufbar.
Einfache Reihen werden direkt auf der Schrankseite angezeigt. Bei noch nicht
konfigurierten Verteilungen erscheint ein klarer leerer Zustand mit Aktion zum
Anlegen der Aufteilung.

Unterverteilungen dürfen zusätzlich den strukturierten Feld-/Bereichsmodus
verwenden. Damit können auch dort Felder, Gerätebereiche, Zählerfelder,
N-/PE-Schienen, DIN-Geräte und Schutzgeräte dokumentiert werden.

Dafür wird die additive Migration `0030_enable_subdistribution_sections`
ausgeführt. Sie entfernt ausschließlich die frühere Einschränkung, nach der
Unterverteilungen zwingend den Reihenmodus verwenden mussten.

## Netzwerkmodul

Der HTTP-500-Fehler der Netzwerkseite wurde behoben. Ursache war eine fehlende
Enum-Einbindung bei der Erstellung der Netzwerkübersicht. Zusätzlich werden
unbekannte oder ältere Enum-Werte kontrolliert auf neutrale Standardwerte
abgebildet.

Die Netzwerkseite lädt ihre Teilbereiche nun fehlertolerant: Scheitert ein
Einzelendpunkt, bleiben erfolgreich geladene Geräte, IP-Netze, Schnittstellen,
Verbindungen oder Topologiedaten sichtbar. Freie Switch-Ports bleiben ein
neutraler Zustand; die Verkabelungsprüfung bleibt gerätebezogen.

## Globale Benachrichtigungen

Eine globale Warteschlange zeigt Erfolg-, Warn- und Fehlermeldungen oberhalb von
Dialogen und Vollbilddialogen an. Fehlermeldungen bleiben länger sichtbar,
können manuell geschlossen werden und werden nacheinander dargestellt.

Bei der mobilen Zählerstandserfassung bleibt der Dialog bei einem Speicherfehler
mit allen Eingaben geöffnet. Während des Requests ist die Speichern-Schaltfläche
gesperrt; nach erfolgreichem Speichern schließt der Dialog und die Bestätigung
ist sichtbar.

## Kompatibilität

- Ausgangsbasis: DocOfHome 1.2.3;
- neuer Alembic-Head: `0030`;
- bestehende Assets, Verteilungen, Netzwerkdaten, Zähler, HA-Zuordnungen und
  Produktbilder bleiben erhalten;
- keine Änderung an der Docker-/Compose-Architektur;
- der bestehende Einzelcontainer und `compose.yaml` bleiben gültig.

## Build-Korrektur

Die neu hinzugefügten Frontend-Regressionsprüfungen verwenden Vite-`?raw`-
Imports zum Einlesen der geprüften Vue-Quelldateien. Damit werden die Tests
weiterhin von `vue-tsc` erfasst, ohne `node:fs` oder zusätzliche
`@types/node`-Deklarationen zu benötigen. Der Docker-Schritt `npm run build`
bricht dadurch nicht mehr mit `TS2307` an den fünf neuen Testdateien ab.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.2.4.md

Stand: 24.07.2026

- Ausgangsbasis: `DocOfHome-1.2.3.zip`
- Zielversion: `1.2.4`
- Datenbankbasis: Alembic `0029`
- neuer Alembic-Head: `0030`
- Prüfplattform: Python 3.13.5, Node.js 22.16.0, npm 10.9.2,
  TypeScript 5.8.3

Dieser Bericht trennt bestandene Prüfungen von Prüfungen, die in der
bereitgestellten Ausführungsumgebung nicht möglich waren. Nicht ausgeführte
Tests werden nicht als bestanden gewertet.

## Umgesetzte Regressionen

### Online-Produktbildsuche

- Backend-Suche bleibt der erste Suchweg.
- Bei Netzwerkfehlern, HTTP 502 oder HTTP 5xx wird auf die Wikimedia-Suche im
  Browser mit `origin=*` gewechselt.
- Bild- und Quell-URLs werden ausschließlich für freigegebene Wikimedia-Hosts
  akzeptiert.
- Vorherige Such- und Importvorgänge werden bei einem neuen Vorgang abgebrochen.
- Suche, Bilddownload und lokaler Upload besitzen Zeitlimits.
- Der ausgewählte Treffer wird über den vorhandenen Upload-Endpunkt lokal in
  DocOfHome gespeichert, wenn der Container das Bild nicht selbst laden kann.
- Fehlerzustände für Backend-Ausfall, externen Ausfall, leere Trefferlisten und
  fehlgeschlagenen Download beziehungsweise Upload sind sichtbar.

### Schrankaufteilung

- Die Schrankaufteilung ist aus jeder aktiven Haupt- und Unterverteilung
  erreichbar.
- Einfache Reihenaufteilungen werden auf der Schrankseite angezeigt.
- Noch nicht konfigurierte Verteilungen zeigen einen leeren Zustand mit Aktion
  zum Anlegen.
- Unterverteilungen dürfen den Feld-/Bereichsmodus verwenden.
- Migration `0030` entfernt ausschließlich die frühere Einschränkung für den
  Aufbau einer Unterverteilung.

### Netzwerkseite

- Die fehlende Einbindung von `NetworkInterfaceType`, die beim Erzeugen der
  Netzwerkübersicht einen `NameError` verursachen konnte, wurde ergänzt.
- Ältere oder unbekannte Enum-Werte werden beim Lesen auf neutrale Werte
  abgebildet.
- Die sieben Seitenanfragen werden fehlertolerant geladen; erfolgreich geladene
  Teilbereiche bleiben bei einem Einzelfehler sichtbar.
- Die bestehende Regel bleibt unverändert: freie Switch-Ports sind neutral und
  die Verkabelungsprüfung erfolgt auf Geräteebene.

### Globale Benachrichtigungen

- Globale FIFO-Warteschlange für Erfolg, Fehler, Warnung und Information.
- Darstellung oben mittig mit `z-index: 10000`, oberhalb von Dialogen und
  Vollbilddialogen.
- Fehler bleiben länger sichtbar als Erfolgsmeldungen und können manuell
  geschlossen werden.
- Bei der mobilen Zählerstandserfassung bleibt der Dialog bei einem Fehler mit
  den Eingaben geöffnet. Während des Requests sind Ladezustand und Sperre der
  Speichern-Schaltfläche aktiv. Nach Erfolg schließt der Dialog und die
  Bestätigung wird global angezeigt.

## Tatsächlich bestandene Prüfungen

| Prüfung | Ergebnis |
|---|---|
| `python3 scripts/check-version.py` | Bestanden; Versionsquellen sind `1.2.4` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden; 10 bestehende Fix-Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| `python3 scripts/check-release-1.2.4.py` | Bestanden; statische Verträge der vier Fehlerkorrekturen vorhanden |
| `python3 scripts/check-migration-0030.py` | Bestanden; Upgrade, Downgrade und erneutes Upgrade gegen eine repräsentative SQLite-0029-Tabelle |
| `python3 -m compileall -q backend/app backend/tests backend/migrations scripts` | Bestanden |
| TypeScript-Transpilierung aller `.ts`-Dateien und aller Vue-`script setup`-Blöcke | Bestanden; keine Syntaxdiagnosen |
| `tsc --noEmit ... productImageSearch.ts frontend/src/types/assets.ts` | Bestanden; strikte semantische Prüfung des neuen Browser-Fallback-Dienstes |
| `git diff --check` | Bestanden; keine Whitespacefehler |
| lokale Markdown-Linkprüfung | Bestanden |
| grundlegende Prüfung auf private Schlüssel und produktive `.env`-Dateien | Bestanden; bekannte Testwerte sind keine produktiven Zugangsdaten |

Die eigenständige Migrationsprüfung verwendet die echte Upgrade- und
Downgrade-Funktion aus
`0030_enable_subdistribution_sections.py`. Dabei wurde geprüft, dass die
0029-Beschränkung vor dem Upgrade greift, nach dem Upgrade entfernt ist, beim
Downgrade wieder angelegt wird und vorhandene Bezeichnungen erhalten bleiben.

## Hinzugefügte Tests

Backend:

- Regressionstest für alle sieben von der Netzwerkseite verwendeten Endpunkte;
- Fallbacktests für alte oder unbekannte Netzwerk-Enum-Werte;
- Unterverteilung mit leerer und gefüllter Feldaufteilung;
- vollständiger Migrations-Rundlauf `0029 -> 0030 -> 0029 -> 0030`;
- Wikimedia-Timeout, HTTP-Fehler und nicht freigegebene Treffer-Hosts.

Frontend:

- Wikimedia-CORS-Suche, Hostfilter, Download und Ausfallfälle;
- Backend-zuerst- und Browser-Fallback-Vertrag der Produktbildkomponente;
- FIFO-Warteschlange, manuelles Schließen und unterschiedliche Anzeigedauer;
- globale Darstellung oberhalb von Dialogen;
- Verhalten des mobilen Zählerdialogs bei Erfolg und Fehler;
- Erreichbarkeit der Schrankaufteilung und leerer Zustand;
- fehlertolerantes Laden der Netzwerkseite.

Die Tests sind Bestandteil des Releases. Ihre vollständige Ausführung war in
dieser Umgebung aus den nachfolgend dokumentierten Gründen nicht möglich.

## Nicht vollständig ausführbare Prüfungen

### Backend-Testlauf

Der Aufruf

```text
python3 -m pytest backend/tests
```

endete beim Laden von `conftest.py` mit:

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

Ein Installationsversuch über die bereitgestellte Paketquelle schlug bereits
bei den Build-Abhängigkeiten mit einer nicht verfügbaren Paketquelle fehl. Ein
Versuch über die öffentliche PyPI-Adresse scheiterte an der DNS-Auflösung der
isolierten Umgebung. Deshalb konnten `pytest`, `ruff`, `mypy`, der vollständige
Alembic-Lauf und die Backend-API-Tests hier nicht vollständig ausgeführt werden.

### Frontend-Test und Build

Der korrekte Aufruf von `npm ci` im Verzeichnis `frontend` endete mit:

```text
npm error code E503
npm error 503 Service Temporarily Unavailable
```

Betroffen war der Download eines Pakets aus der bereitgestellten npm-Registry.
Dadurch standen `node_modules`, `vitest`, `vue-tsc`, Vite und die MDI-CSS-Datei
nicht vollständig zur Verfügung. Folgende Prüfungen konnten deshalb nicht
vollständig ausgeführt werden:

- `npm test`;
- `npm run build`;
- die vollständige MDI-Prüfung gegen `@mdi/font`;
- der produktive Vite-Build.

Als Ersatz wurden alle TypeScript- und Vue-Skriptblöcke syntaktisch geprüft und
der neu hinzugefügte browserseitige Wikimedia-Dienst mit dem vorhandenen
globalen TypeScript-Compiler streng geprüft. Dies ersetzt keinen vollständigen
Vue-/Vite-Build.

### Docker

`docker --version` endete mit `docker: command not found`. Daher waren

- `docker compose build`;
- Containerstart und Healthcheck;
- Prüfung der Backend-Logs im gebauten Image;
- praktische End-to-End-Tests im Browser

in dieser Umgebung nicht möglich.

## Performance- und Stabilitätsprüfung

Quellseitig geprüft und berücksichtigt wurden:

- Abbruch überholter Online-Suchen und Bildimporte;
- Zeitlimits für externe Suche, Download und Upload;
- kein dauerhafter externer Bildbezug nach Auswahl;
- kein vollständiger Ausfall der Netzwerkseite bei einem fehlerhaften
  Einzelendpunkt;
- keine zusätzliche Docker-, Datenbank- oder Worker-Architektur;
- keine neue Datenmigration außer der notwendigen Entfernung einer einzelnen
  Check-Constraint;
- keine Änderung an der neutralen Behandlung freier Switch-Ports;
- keine neuen blockierenden Schleifen oder periodischen Frontend-Requests in den
  geänderten Bereichen.

Eine belastbare Laufzeitmessung, SQL-Abfragezählung oder Browser-Profilierung war
ohne lauffähigen Gesamtbuild nicht möglich.

## Erforderliche Nachprüfung in einer vollständigen Build-Umgebung

Vor produktivem Einsatz sollten die CI-Schritte aus `.github/workflows/ci.yml`
ausgeführt werden:

```text
backend:  pip install -r requirements-dev.txt
          ruff check app tests
          mypy app
          python -m pytest -q
          alembic upgrade head

frontend: npm ci --ignore-scripts --no-audit --no-fund
          npm test
          npm run build

docker:   docker compose build
          docker compose up -d
          Healthcheck und Logs prüfen
```

Danach sind die vier gemeldeten Abläufe praktisch zu testen: Produktbildsuche
mit Backend und Browser-Fallback, Schrankaufteilung einer Unterverteilung,
Netzwerkseite mit vorhandenem Datenbestand sowie Zählerstandserfassung auf einem
kleinen Mobilbildschirm.

## Bewertung

Die vier Fehlerbereiche sind im Quellstand umgesetzt und durch statische
Prüfungen sowie eine eigenständige echte Migrationsprüfung abgesichert. Das
Release wird bewusst **nicht** als vollständig Docker- und End-to-End-validiert
bezeichnet, weil Paketquellen und Docker in der Ausführungsumgebung nicht
verfügbar waren.
## 1.2.3 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.2.3 behebt einen TypeScript-Buildfehler aus 1.2.2.

## Korrektur

Nach erfolgreicher MDI-Prüfung brach `vue-tsc --noEmit` in
`frontend/src/services/immichGallery.test.ts` ab. Das dort verwendete
Konfigurationsobjekt entsprach nicht mehr `ConfigurationRead`, weil das in 1.2.0
ergänzte Pflichtfeld `online_product_image_search_enabled` fehlte.

Das Test-Fixture enthält dieses Feld nun explizit. Zusätzlich wurde der
Funktionsparameter von `selectedImmichAlbumId` auf
`Pick<ConfigurationRead, 'integrations'>` begrenzt. Die Funktion benötigt nur
die Integrationsliste und ist damit nicht länger unnötig an sämtliche
Konfigurationsfelder gekoppelt.

## Technische Auswirkungen

- keine Änderung an Backend, API oder Datenmodell;
- keine neue Datenbankmigration;
- Alembic-Head bleibt `0029`;
- bestehende Daten und Einstellungen bleiben unverändert.

## Update

Ein Update von 1.2.2 auf 1.2.3 erfordert den üblichen Image-Neubau und
Containerneustart. Vor dem Update bleibt ein vollständiges Backup empfohlen.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.2.3.md

Stand: 24.07.2026  
Ausgangsbasis: DocOfHome 1.2.2  
Alembic-Head: `0029`

## Anlass

Der Docker-/Frontend-Build von 1.2.2 bestand die MDI-Prüfung mit 218 Icons,
brach anschließend jedoch bei `vue-tsc --noEmit` ab. In
`frontend/src/services/immichGallery.test.ts` fehlte im Test-Fixture das
Pflichtfeld `online_product_image_search_enabled` aus `ConfigurationRead`.

## Änderung

- Das Test-Fixture enthält nun
  `online_product_image_search_enabled: false`.
- `selectedImmichAlbumId` akzeptiert nur noch
  `Pick<ConfigurationRead, 'integrations'>`, weil die Funktion ausschließlich
  die Integrationsliste benötigt.
- Backend, API, Datenmodell und Migrationen wurden nicht verändert.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| gezielte TypeScript-Prüfung mit globalem TypeScript 5.x für `settings.ts`, `immich.ts`, `immichGallery.ts` und `immichGallery.test.ts` | Bestanden |
| Kontrolle des Test-Fixtures auf `online_product_image_search_enabled` | Bestanden |
| Kontrolle des eingeschränkten Funktionsparameters auf `Pick<ConfigurationRead, 'integrations'>` | Bestanden |
| `python3 scripts/check-version.py` | Bestanden; alle Versionsquellen `1.2.3` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 -m compileall -q backend/app backend/tests scripts` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden; 10/10 Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| lokale Markdown-Linkprüfung | Bestanden |
| Scan auf Caches, lokale Datenbanken und typische Secret-Dateien | Bestanden |
| Manifestprüfung nach erneutem Entpacken | Bestanden |

## Vom Zielsystem bereits bestätigte Teilprüfung

Der vom Betreiber ausgeführte Docker-Build meldete vor dem TypeScript-Fehler:

```text
218 MDI-Icons geprüft: alle verfügbar.
```

Damit ist der vorherige MDI-Fehler aus 1.2.1/1.2.2 nicht erneut aufgetreten.

## Nicht vollständig ausführbare Prüfungen

### Vollständiger Frontend-Build

Ein erneutes `npm ci` in der isolierten Releaseumgebung scheiterte wiederholt am
internen npm-Paketdienst:

```text
HTTP 503 beim Abruf von why-is-node-running-2.3.0.tgz
```

Dadurch konnten `vitest`, `vue-tsc` über das echte Projekt-Node-Modul und
`vite build` hier nicht vollständig ausgeführt werden. Der konkret gemeldete
Typfehler wurde jedoch mit dem vorhandenen globalen TypeScript-Compiler gezielt
und erfolgreich geprüft.

### Vollständiger Backend-Test

`python3 -m pytest -q` konnte nicht starten, weil `sqlmodel` in der isolierten
Umgebung nicht installiert ist. Der Fehler lautet:

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

Docker ist in dieser Umgebung ebenfalls nicht verfügbar. Diese Prüfungen werden
nicht als bestanden ausgewiesen.

## Datenbank und Migration

1.2.3 enthält keine neue Migration. Alembic-Head bleibt `0029`; ein neuer
Migrations-Roundtrip ist für diesen reinen Frontend-Typprüfungsfix nicht
erforderlich.

## Empfohlene Zielsystemprüfung

1. `docker compose build --no-cache`;
2. prüfen, dass die MDI-Prüfung weiterhin 218 verfügbare Icons meldet;
3. prüfen, dass `vue-tsc --noEmit` den bisherigen Fehler in
   `immichGallery.test.ts` nicht mehr meldet;
4. Vite-Build vollständig bis zum Ende ausführen;
5. Container starten und Immich-Auswahl sowie Einstellungen öffnen;
6. anschließend die üblichen Backend-, Frontend- und Smoke-Tests ausführen.

## Gesamturteil

Der konkret gemeldete TypeScript-Buildfehler aus 1.2.2 ist im Quellstand von
1.2.3 korrigiert. Die Typabhängigkeit wurde zusätzlich fachlich eingegrenzt,
damit unabhängige Konfigurationserweiterungen diesen Test nicht erneut brechen.
API, Datenmodell und Migrationen bleiben unverändert. Die vollständige
Zielsystemprüfung muss im Docker-/CI-System mit installierten Abhängigkeiten
erfolgen.
## 1.2.2 – 2026-07-24

### Changelog

### Korrigiert

- Frontend-Buildfehler in der MDI-Prüfung behoben: Das in `@mdi/font` 7.4.47
  nicht vorhandene `mdi-label-plus-outline` wurde im Asset-Labeldialog an beiden
  Stellen durch `mdi-tag-plus-outline` ersetzt.
- Versions- und Releasedokumentation auf 1.2.2 aktualisiert.

### Kompatibilität

- keine Änderung an API oder Datenmodell;
- keine neue Alembic-Migration; Head bleibt `0029`;
- direkter Patch von 1.2.1 ohne Datenmigration.

### Release Notes

DocOfHome 1.2.2 behebt einen Frontend-Buildfehler aus 1.2.1.

## Korrektur

Die verpflichtende MDI-Prüfung meldete:

```text
Nicht verfügbare MDI-Icons: mdi-label-plus-outline
```

Das Icon wurde im Button und im Dialog zur Inline-Anlage von Asset-Labels durch
`mdi-tag-plus-outline` ersetzt. Dieses Icon ist in der festgeschriebenen
Abhängigkeit `@mdi/font` 7.4.47 vorhanden und beschreibt die Aktion fachlich
passend.

## Technische Auswirkungen

- keine Änderung an Backend, API oder Datenmodell;
- keine neue Datenbankmigration;
- Alembic-Head bleibt `0029`;
- bestehende Daten und Einstellungen bleiben unverändert.

## Update

Ein Update von 1.2.1 auf 1.2.2 erfordert den üblichen Image-Neubau und
Containerneustart. Vor dem Update bleibt ein vollständiges Backup empfohlen.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.2.2.md

Stand: 24.07.2026  
Ausgangsbasis: DocOfHome 1.2.1  
Alembic-Head: `0029`

## Anlass

Der Docker-/Frontend-Build von 1.2.1 brach in
`frontend/scripts/check-mdi-icons.mjs` ab, weil
`mdi-label-plus-outline` in der festgeschriebenen Abhängigkeit `@mdi/font`
7.4.47 nicht enthalten ist.

## Änderung

In `frontend/src/pages/AssetEditorPage.vue` wurden beide Vorkommen durch
`mdi-tag-plus-outline` ersetzt. Backend, API, Modelle und Migrationen wurden
nicht verändert.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Suche nach `mdi-label-plus-outline` im Releasequellstand | Bestanden; kein Vorkommen mehr |
| Kontrolle beider Label-Aktionen auf `mdi-tag-plus-outline` | Bestanden; zwei Vorkommen |
| Abgleich mit der Iconliste von `@mdi/font` 7.4.47 | Bestanden; `mdi-tag-plus-outline` ist enthalten |
| `python3 scripts/check-version.py` | Bestanden; alle Versionsquellen `1.2.2` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 -m compileall -q backend/app backend/tests scripts` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| lokale Markdown-Linkprüfung | Bestanden |
| Scan auf Caches, lokale Datenbanken und Secrets | Bestanden |
| Manifestprüfung nach erneutem Entpacken | Bestanden |

## Nicht vollständig ausführbare Prüfungen

In der isolierten Releaseumgebung fehlen die vollständigen installierten npm-
und Python-Abhängigkeiten sowie Docker. Deshalb werden `npm ci`, `npm run build`,
Vitest, vollständiges Pytest, Ruff, mypy und Docker-Build hier nicht als
bestanden ausgewiesen. Der vom Betreiber gemeldete Buildabbruch liegt jedoch vor
dem TypeScript-/Vite-Schritt und wurde direkt an der vom Prüfer beanstandeten
Iconreferenz korrigiert.

## Datenbank und Migration

1.2.2 enthält keine neue Migration. Alembic-Head bleibt `0029`; ein neuer
Migrations-Roundtrip ist für diesen reinen Frontend-Patch nicht erforderlich.

## Empfohlene Zielsystemprüfung

1. `docker compose build --no-cache`;
2. prüfen, dass die MDI-Prüfung alle Icons als verfügbar meldet;
3. Container starten und Asset-Editor öffnen;
4. Inline-Labeldialog öffnen und ein Testlabel anlegen;
5. danach die üblichen Backend-, Frontend- und Smoke-Tests ausführen.

## Gesamturteil

Der konkrete MDI-Buildfehler aus 1.2.1 ist im Quellstand von 1.2.2 korrigiert.
API, Datenmodell und Migrationen bleiben unverändert. Die vollständige
Zielsystemprüfung muss im Docker-/CI-System mit installierten Abhängigkeiten
erfolgen.
## 1.2.1 – 2026-07-24

### Changelog

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

### Release Notes

DocOfHome 1.2.1 ist ein reines Dokumentations- und Statuspflege-Release auf
Basis von 1.2.0.

## Was wurde bereinigt?

- `PROJECT_STATUS.md` beschreibt jetzt eindeutig den aktuellen Release- und
  Freigabestatus.
- Der aktuelle Backlog besitzt eine eigene, datumsunabhängige Datei.
- Ein zentrales Sprintregister trennt historische Sprintverträge von aktiven
  oder geplanten Sprints.
- Der frühere Projektplan für `0.1.18-dev` bleibt vollständig im Archiv, wird
  aber nicht mehr als aktueller Plan angezeigt.
- Sprint 0039 für eine Info-, Changelog-, Impressums- und Feedbackseite ist als
  **Draft / Planning only** dokumentiert.
- Offene Zielsystem- und CI-Prüfungen von 1.2.x sind klar von Funktionssprints
  getrennt.

## Technische Auswirkungen

- keine Änderung an Anwendungscode oder API;
- keine neue Datenbankmigration;
- Alembic-Head bleibt `0029`;
- keine Änderung an bestehenden Daten oder Integrationskonfigurationen.

## Update

Ein Update von 1.2.0 auf 1.2.1 erfordert nur den üblichen Image-Neubau und
Containerneustart. Vor jedem Update bleibt ein vollständiges Backup empfohlen.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.2.1.md

Stand: 24.07.2026  
Ausgangsbasis: DocOfHome 1.2.0  
Alembic-Head: `0029`

## Umfang

DocOfHome 1.2.1 ist ein Dokumentations- und Statuspflege-Release. Es wurden
keine fachlichen Funktionen, API-Verträge, Migrationen oder produktiven
Quellcodedateien geändert. Angepasst wurden zentrale Versionsquellen sowie
Projekt-, Roadmap-, Sprint-, Release- und Qualitätsdokumentation.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| `python3 scripts/check-version.py` | Bestanden; alle Versionsquellen `1.2.1` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 -m compileall -q backend/app backend/tests scripts` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden; 10/10 Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| Vergleich mit dem entpackten 1.2.0-Quellstand | Nur freigegebene Dokumentations- und Versionsdateien verändert |
| Archivvergleich des alten Projektstatus | Original vollständig und bytegleich erhalten |
| Archivvergleich des frühen Audits | Original vollständig und bytegleich erhalten |
| lokale Markdown-Linkprüfung | Bestanden |
| Scan auf generierte Caches und lokale Secrets | Bestanden; keine Release-Reste gefunden |
| Manifestprüfung nach erneutem Entpacken | Bestanden |

## Nicht vollständig ausführbare Prüfungen

### Backend

`pytest` ist vorhanden, die Testsammlung bricht jedoch wegen der nicht
installierten Laufzeitabhängigkeit `sqlmodel` ab. `ruff` und `mypy` sind in der
Ausführungsumgebung nicht installiert. Es wird daher kein vollständiger
Backend-Testlauf als bestanden ausgewiesen.

### Frontend

Node.js 22 und npm 10 sind vorhanden, aber `node_modules` fehlt. Ein bewusst
offline ausgeführtes `npm ci --offline --ignore-scripts` scheitert, weil nicht
alle Pakete im lokalen Cache liegen. Vitest, `vue-tsc` und der Vite-Build konnten
daher nicht ausgeführt werden.

### Docker

Docker ist in der Ausführungsumgebung nicht installiert. Ein Image- und
Container-Smoke-Test war nicht möglich.

## Datenbank und Migration

1.2.1 enthält keine neue Migration. Alembic-Head bleibt `0029`. Die bereits für
1.2.0 dokumentierte Kette bis 0029 wird nicht durch dieses Patch-Release
verändert. Da keine Schema- oder Modelldateien geändert wurden, war kein neuer
Migrations-Roundtrip erforderlich.

## Dokumentationsbereinigung

Geprüft wurde insbesondere:

- `PROJECT_STATUS.md` benennt 1.2.1, Head 0029 und keinen aktiven Sprint;
- `docs/CURRENT_STATUS_AND_BACKLOG.md` ist die aktuelle Backlogquelle;
- `docs/SPRINT_REGISTER.md` trennt historische Verträge von aktuellen Sprints;
- Sprint 0039 ist `Draft / Planning only` und kein Implementierungsauftrag;
- der alte Status `0.1.18-dev` liegt vollständig unter `docs/archive`;
- der frühere Root-Audit liegt vollständig unter `docs/archive`;
- README, Roadmap, Changelog und Release Notes verweisen auf 1.2.1;
- historische Sprintverträge wurden nicht rückwirkend verändert.

## Empfohlene Zielsystemprüfung

Vor einem produktiven Einsatz von 1.2.x weiterhin durchführen:

1. vollständiges Backup des persistenten Datenordners;
2. `ruff`, `mypy` und vollständiges `pytest` in der Projektumgebung;
3. `npm ci`, Vitest, `vue-tsc` und Vite-Build;
4. Docker-Build und Containerstart;
5. Start mit einer Kopie der bestehenden Datenbank;
6. reale HA-Bedienprüfung mit mehreren Tausend Entitäten.

## Gesamturteil

Das Release ist als Dokumentations- und Statuspflegepaket konsistent. Die
historischen Inhalte bleiben erhalten, während der aktuelle Projektplan nun
eindeutig ist. Vollständige anwendungsbezogene Backend-, Frontend- und
Dockerprüfungen bleiben wegen fehlender lokaler Abhängigkeiten ein Zielsystem-
oder CI-Gate und werden nicht als bestanden behauptet.
## 1.2.0 – 2026-07-23

### Changelog

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

### Release Notes

DocOfHome 1.2.0 setzt die vollständige Aufgabenübergabe auf Basis von 1.1.3 um
und konzentriert sich auf große Home-Assistant-Installationen, bessere
Asset-Workflows und eine fachlich genauere Zählerschrankdarstellung.

## Höhepunkte

- sofort bedienbare HA-Oberfläche ohne Tausende gleichzeitig gerenderte Entitäten
- 50 Geräte beziehungsweise 100 Entitäten pro serverseitig gefilterter Seite
- ein gebündelter HA-Sync, 15 Minuten Registercache und 30 Sekunden Livecache
- mehrere HA-Geräte und Entitäten je Asset mit Rollen
- Smart Meter und andere DIN-Produkte mit TE-Breite und Livewert im Schrank
- N und PE auf derselben Ebene links/rechts
- Produktbilder per Upload, Immich, optionaler Wikimedia-Suche oder URL
- Assets duplizieren oder als nummerierte Serie mit optionaler TE-Platzierung anlegen
- Labels direkt im Asset-Formular erstellen
- seltene Navigationseinträge unter **Mehr**

## Update

Vor dem Update ein DocOfHome-Backup und eine externe Kopie des gesamten
persistenten `data`-Ordners erstellen. Beim Start migriert Alembic von `0028`
auf `0029`. Details stehen in `docs/MIGRATION_GUIDE_1.2.0.md`.

## Kompatibilität

Alle in 1.1.0 bis 1.1.3 eingeführten Funktionen bleiben erhalten. Bestehende
HA-Zuordnungen, Zähler, Elektro- und Netzwerkdaten, Produktbilder, Labels und
Dokumentverknüpfungen werden nicht gelöscht. Das PE-Icon bleibt `mdi-earth`.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.2.0.md

Stand: 23.07.2026  
Ausgangsbasis: DocOfHome 1.1.3  
Alembic-Head: `0029`

## Ergebnisübersicht

DocOfHome 1.2.0 wurde aus dem freigegebenen Stand 1.1.3 erstellt. Die neuen
Datenbankänderungen, Python- und TypeScript-Syntax, Versionsangaben, bestehende
Projektprüfungen sowie das Releasepaket wurden geprüft. Vollständige Backend-
und Frontend-Testläufe waren in der isolierten Build-Umgebung nicht möglich,
weil die Ausgangs-ZIP keine installierten Abhängigkeiten enthält und der
Paketserver nicht erreichbar war. Nicht ausgeführte Prüfungen werden daher
nicht als bestanden ausgewiesen.

## Umgesetzte Funktionsbereiche

- Home-Assistant-Seite mit echter serverseitiger Pagination, serverseitigen
  Filtern, verzögertem Laden und dauerhaftem Mehrfachauswahlzustand.
- Gebündelter Home-Assistant-Abgleich mit Single-Flight-Sperre, 15 Minuten
  Registercache und 30 Sekunden Livezustandscache.
- Mehrere HA-Geräte und HA-Entitäten pro Asset einschließlich Entitätsrollen.
- Allgemeine DIN-Hutschienengeräte mit TE-Breite, Platzierung und Livewerten.
- N- und PE-Schienen auf derselben Ebene mit eindeutiger Seite links/rechts.
- Produktbild-Upload, Immich-Auswahl, kontrollierbare Wikimedia-Suche,
  manueller URL-Eingabe, Vorschau und Entfernen.
- Asset-Duplizierung und Serienanlage mit optionaler fortlaufender Platzierung.
- Inline-Anlage von Labels im Asset-Formular.
- Aufklappbare Navigation „Mehr“.
- Gzip-Komprimierung größerer Antworten und Reduktion mehrerer N+1-Abfragen.

## Tatsächlich ausgeführte Prüfungen

### Python und Projektverträge

| Prüfung | Ergebnis |
|---|---|
| `python3 -m compileall -q backend/app backend/migrations/versions backend/tests scripts` | Bestanden |
| `python3 scripts/check-version.py` | Bestanden, alle Versionsquellen `1.2.0` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden, 10/10 Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| `git diff --check` | Bestanden |
| Suche nach `mdi-ground-wire` in produktivem Quellcode | Kein Treffer |
| Pydantic-Vertragsprüfungen für DIN-Produkte, Bereichsseiten, Serienplatzierung und primäre HA-Rolle | Bestanden |

### Migrationen

Die Migration wurde mit Alembics `MigrationContext` und `Operations` direkt
gegen temporäre SQLite-Datenbanken ausgeführt. Dadurch konnte die eigentliche
DDL- und Datenmigration unabhängig von der nicht verfügbaren SQLModel-
Laufzeit geprüft werden.

| Kette | Ergebnis |
|---|---|
| Leere Datenbank → Migration 0029 | Bestanden |
| Bestehender Stand 0028 → 0029 | Bestanden |
| 0029 → 0028 | Bestanden |
| 0028 → 0029 erneut | Bestanden |

Zusätzlich geprüft:

- Neue Produktfelder und die Einstellung für die Online-Bildsuche werden angelegt.
- Bestehende HA-Zuordnungen erhalten die Rolle `additional`.
- Bestehende halbe Schrankbereiche werden verlustfrei auf `links` migriert.
- Eine rechte Hälfte auf derselben Ebene kann danach angelegt werden.
- Doppelte linke/rechte Belegungen und Überdeckung durch volle Bereiche werden
  durch Constraints beziehungsweise Trigger verhindert.
- Beim Downgrade werden kollidierende Ebenen vor Entfernung des Seitenfelds auf
  eindeutige Positionen verschoben, sodass beide Bereiche erhalten bleiben.
- Die Tabelle für allgemeine DIN-Asset-Platzierungen wird korrekt angelegt und
  beim Downgrade entfernt.

### Frontend-Syntax

Mit dem global vorhandenen TypeScript-Parser wurden alle `.ts`-Dateien und
alle TypeScript-Skriptblöcke der Vue-Komponenten eingelesen.

- Geprüfte Dateien/Skriptblöcke: 150
- Parserfehler: 0

### Releaseprüfung

Die endgültige Release-ZIP wurde mit reproduzierbarer Dateireihenfolge und
festen ZIP-Zeitstempeln erzeugt und anschließend unabhängig erneut entpackt.

- Projektdateien im Manifest: 491
- Dateien im ZIP einschließlich `RELEASE_MANIFEST.txt`: 492
- `.git`, `node_modules`, `__pycache__`, `.pytest_cache`, Build-Caches,
  temporäre Datenbanken und echte `.env`-Dateien: nicht enthalten
- Interne Manifestdatei mit SHA-256 und Dateigröße jeder Projektdatei: geprüft
- Externe Manifestkopie: identisch mit der internen Manifestdatei
- Externe SHA-256-Prüfsumme des ZIP-Archivs: erzeugt und gegengeprüft
- ZIP-CRC-Prüfung: bestanden
- Jede Manifestzeile gegen die unabhängig entpackte Datei: bestanden
- Zusätzliche oder fehlende Projektdateien gegenüber dem Manifest: keine

## Ergänzte Regressionstests

Folgende automatisierte Tests wurden dem Projekt hinzugefügt oder erweitert:

- HA-Mehrfachzuordnung, Rollen und Konfliktschutz.
- Pagination und Filterung mit 5.000 simulierten HA-Entitäten.
- Single-Flight-Verhalten bei parallelen HA-Synchronisierungen.
- Asset-Duplikate und Serien ohne Übernahme eindeutiger Kennungen.
- N-/PE-Seitenkonflikte und volle Bereiche.
- Allgemeine DIN-Platzierung und Produkt-TE-Breite.
- Produktbildsignaturen und Einschränkung des Online-Imports auf Wikimedia.

Diese Tests sind Bestandteil des Releases, konnten in dieser Umgebung jedoch
nicht vollständig ausgeführt werden.

## Nicht ausführbare Prüfungen

### Pytest, Ruff und Mypy

- `pytest -q` wurde gestartet, brach aber bereits beim Laden von `conftest.py`
  mit `ModuleNotFoundError: No module named 'sqlmodel'` ab.
- Ein Installationsversuch für `sqlmodel` scheiterte, weil der konfigurierte
  Paketserver in der isolierten Umgebung nicht erreichbar war.
- `ruff` und `mypy` sind in der Umgebung nicht installiert.

Daher gibt es keinen behaupteten vollständigen Backend-Test-, Ruff- oder
Mypy-Erfolg. Die Python-Kompilierung und die direkten Migrationsprüfungen sind
bestanden.

### NPM-Test und Produktionsbuild

- `npm ci --offline --ignore-scripts` scheiterte, weil benötigte Pakete nicht im
  lokalen NPM-Cache vorhanden waren.
- `npm run build` wurde gestartet, konnte aber ohne `node_modules` bereits bei
  der MDI-CSS-Prüfung nicht fortfahren.
- Der TypeScript-Parserlauf ersetzt keine vollständige `vue-tsc`-, Vitest- oder
  Vite-Buildprüfung.

Daher gibt es keinen behaupteten vollständigen Frontend-Test oder
Produktionsbuild.

### Docker-Build

Docker ist in der Ausführungsumgebung nicht installiert. Ein Docker-Build
konnte nicht ausgeführt werden.

## Performancebewertung

Die Hauptursache der langsamen HA-Seite in 1.1.3 war nicht nur die Datenmenge,
sondern dass das Frontend paginierte Antworten bis zur letzten Seite erneut
zusammenführte und anschließend alle Entitäten renderte. Zusätzlich konnte ein
manueller Refresh über mehrere API-Aufrufe mehrere vollständige Abgleiche
anstoßen.

In 1.2.0 gilt:

- Geräte: standardmäßig 50 Datensätze je API-Seite.
- Entitäten: standardmäßig 100 Datensätze je API-Seite.
- Entitäten werden erst beim Öffnen des Bereichs, bei einer Suche oder für ein
  ausgewähltes Gerät geladen.
- Suche, Bereich, Domain, Gerät, Geräteklasse, Einheit und Verfügbarkeit werden
  im Backend gefiltert.
- „Nur ausgewählte Entitäten“ lädt nur die ausgewählten Datensätze.
- Ein Refresh stößt nur einen gebündelten Abgleich an; parallele Anforderungen
  warten auf denselben Lauf.
- Registerdaten und Livezustände besitzen getrennte Cachezeiten.
- Mehrere Asset-, Platzierungs- und Livewertansichten verwenden gebündelte
  Datenbankabfragen statt wiederholter Einzelabfragen.

Ein reproduzierbarer Browser-Lauf mit einem realen Home-Assistant-System und
5.000 Entitäten war in dieser Umgebung nicht möglich. Der enthaltene Testfall
für 5.000 Entitäten muss nach Installation der Projektabhängigkeiten in CI oder
auf dem Zielsystem ausgeführt werden.

## Empfohlene Zielsystemprüfung vor produktivem Rollout

1. Sicherung der produktiven Datenbank und des Datenverzeichnisses erstellen.
2. Release zunächst in einer Testinstanz mit einer Kopie der Datenbank starten.
3. Migration auf 0029 prüfen und N-/PE-Bereiche visuell kontrollieren.
4. HA-Seite mit dem realen System öffnen, suchen, Seiten wechseln und einen
   manuellen Refresh ausführen.
5. Mehrfachzuordnungen, Livewerte, Produktbilder und Serienanlage mit wenigen
   Beispieldatensätzen prüfen.
6. Danach erst das produktive Update durchführen.

## Gesamturteil

Der Quellstand ist statisch konsistent, die Datenbankmigration einschließlich
Upgrade-/Downgrade-Zyklus ist praktisch geprüft und die Releaseartefakte wurden
gegen ihr Manifest validiert. Wegen der nicht verfügbaren Python- und
Node-Abhängigkeiten bleibt der vollständige automatisierte Anwendungs-,
Frontend- und Docker-Build als Zielsystem-/CI-Prüfung offen.
## 1.1.3 – 2026-07-23

### Changelog

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

### Release Notes

Veröffentlicht am 23. Juli 2026.

DocOfHome 1.1.3 ist ein Build-Korrekturrelease für 1.1.2. Es enthält den
vollständigen Funktionsumfang von 1.1.2 unverändert und behebt den Abbruch des
Frontend-Builds bei der MDI-Icon-Prüfung.

## Korrigiert

- Das nicht in `@mdi/font` 7.4.47 vorhandene Icon `mdi-ground-wire` wurde bei
  der PE-Schiene durch das verfügbare und fachlich passende Icon `mdi-earth`
  ersetzt.
- Der Docker-Build kann dadurch die vorgeschaltete Prüfung
  `scripts/check-mdi-icons.mjs` passieren und anschließend mit Vue-TSC und Vite
  fortfahren.
- Der GitHub-CI-Workflow verwendet für das Frontend nun wie der Docker-Build
  `npm ci`, damit exakt die in `package-lock.json` festgeschriebenen Versionen
  geprüft werden.

## Datenbank und Kompatibilität

- Keine neue Datenbankmigration.
- Alembic-Head bleibt `0028_collected_integration_fixes`.
- Bestehende Daten und Konfigurationen aus 1.1.2 bleiben unverändert.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.1.3.md

Stand: 23. Juli 2026

## Ursache

Der Docker-Build von 1.1.2 brach in `npm run build` bereits vor Vue-TSC und Vite
ab. Die vorgeschaltete Prüfung erkannte `mdi-ground-wire` als nicht vorhandenes
Icon in der festgeschriebenen Abhängigkeit `@mdi/font` 7.4.47.

## Korrektur

- einzige Verwendung von `mdi-ground-wire` entfernt;
- PE-Schiene auf `mdi-earth` umgestellt;
- Frontend-, Backend- und Releaseversion auf 1.1.3 vereinheitlicht;
- GitHub-CI von `npm install` auf das reproduzierbare `npm ci` umgestellt;
- keine Änderung an Datenmodell oder Migrationen.

## Lokal ausgeführte Prüfungen

- Quelltextsuche: keine verbleibende Verwendung von `mdi-ground-wire`;
- PE-Schienen-Konfiguration verwendet exakt `mdi-earth`;
- Versionskonsistenz zwischen `VERSION`, Frontend, Lockdatei und Backend;
- Python-Syntaxprüfung für Anwendung, Migrationen, Tests und Hilfsscripte;
- dependency-freie Vertragsprüfungen für Branding, Ableseerinnerungen und die
  zehn Funktionen aus 1.1.2;
- TypeScript-Syntaxprüfung der `.ts`-Dateien und der Scriptblöcke aus `.vue`
  mit dem lokal vorhandenen TypeScript-Parser;
- vollständige Manifest- und SHA-256-Prüfung nach erneuter Extraktion des
  finalen Release-ZIPs.

## Abhängigkeitsbasierter Build

Die Ausgangs-ZIP enthält keine installierten Node-Module. Gemäß der Vorgabe,
ausschließlich lokal mit dem gelieferten Projekt zu arbeiten, wurden keine
Pakete aus dem Internet nachgeladen. Der vollständige Lauf `npm ci && npm run
build` muss deshalb auf dem Docker-Zielsystem oder in GitHub Actions erfolgen.
Der konkret gemeldete Abbruchpunkt ist im Quellstand beseitigt; der vorhandene
MDI-Prüfschritt bleibt aktiv und schützt weiterhin vor unbekannten Icons.
## 1.1.2 – 2026-07-23

### Changelog

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

### Release Notes

Veröffentlicht am 23. Juli 2026.

DocOfHome 1.1.2 bündelt die zehn nach 1.1.1 gemeldeten Korrekturen und
Erweiterungen. Das Release bleibt vollständig rückwärtskompatibel zu den
Verbrauchs-, Energie-, Elektro-, Asset-, Immich- und Netzwerkdaten aus 1.1.1.

## Zähler und Home Assistant

- Verbrauchszähler können mit einem vorhandenen Asset und einem Ort verknüpft
  werden. Fehlt ein eigener Ort, wird der Ort des zugeordneten Assets angezeigt.
- Pro Zähler können zusätzlich zur kumulativen Ablese-Entität je eine
  Home-Assistant-Entität für aktuelle Gesamtleistung und Spannung gewählt
  werden.
- Die Zählerübersicht zeigt verfügbare Livewerte in Watt und Volt. Initiale
  Abfragen teilen sich den lokalen HA-Snapshot; die Aktualisieren-Schaltfläche
  erzwingt einen frischen Abruf. Ein Ausfall von Home Assistant verhindert weder
  manuelle Ablesungen noch die restliche Zählerverwaltung.
- Verbrauchszähler können in Zählerfeldern eines Zählerschranks platziert,
  verschoben und wieder entfernt werden.
- Noch nicht mit einem Verbrauchszähler verknüpfte Assets vom Typ **Zähler**
  können ebenfalls direkt platziert werden. Eine spätere Doppelplatzierung
  desselben physischen Zählers wird verhindert.

## Assets, Immich und Orte

- Verknüpfte Immich-Bilder in der Asset-Ansicht öffnen sich per Klick oder
  Tastatur in einer großen Vorschau.
- Ortsauswahlen werden hierarchisch nach Gebäude, Etage und den jeweiligen
  Räumen sortiert. Hinterlegte `sort_order`-Werte haben Vorrang; innerhalb
  derselben Ebene wird deutsch-alphabetisch sortiert.

## Zählerschrank und Elektro-Topologie

- Neue Bereichstypen **N-Schiene** und **PE-Schiene** stehen zur Verfügung.
- Bereiche können volle oder halbe Breite besitzen. Zwei aufeinanderfolgende
  halbe Bereiche werden im Schrankplan nebeneinander dargestellt.
- Beim Anlegen und Bearbeiten einer elektrischen Verteilung sind ausschließlich
  Assets vom Typ **Elektrische Verteilung** zulässig. Diese Regel wird sowohl
  in der Auswahl als auch serverseitig erzwungen.
- Der in der Energiekonfiguration gepflegte Netzanschluss erscheint als echter
  externer Quellpunkt der Elektro-Topologie und kann beispielsweise mit HAK,
  Hauptsicherung, SLS, Zähler oder Verteilung verbunden werden. Als Ziel ist er
  bewusst nicht zulässig.

## Netzwerk

- Physische Ports können einer virtuellen beziehungsweise logischen
  Schnittstelle wie `LAN-Bridge`, `Management` oder einem VLAN zugeordnet
  werden. Eine Bridge mit Mitgliedsports bleibt vor einem versehentlichen
  Wechsel zu einem physischen Porttyp geschützt.
- IP-Adressen liegen auf der logischen Schnittstelle; eine primäre Adresse wird
  direkt am Gerät angezeigt. Dadurch lassen sich Router, Repeater und Geräte
  mit mehreren LAN-Ports fachlich korrekt abbilden.
- Die bestätigte FRITZ!Box-Übernahme legt für Geräte mit IP eine logische
  Management-/LAN-Schnittstelle an und ordnet den erkannten physischen oder
  drahtlosen Anschluss dieser zu.
- Freie Switch-Ports werden neutral als **Frei** angezeigt. Eine Warnung
  entsteht nur, wenn ein netzwerkfähiges Gerät insgesamt keine aktive
  Verbindung und keinen WLAN-/Mobilfunk-Uplink besitzt.

## Datenbank und Kompatibilität

- Neue Alembic-Revision: `0028_collected_integration_fixes`.
- Die Migration ergänzt nur neue Spalten, Constraints und die Tabelle für
  Zählerplatzierungen. Bestehende Daten bleiben erhalten.
- Der geprüfte Migrationspfad umfasst `0027 -> 0028`, `0028 -> 0027` und ein
  erneutes Upgrade auf `0028`.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.1.2.md

Stand: 23. Juli 2026

## Prüfumfang

Geprüft wurde das gemeinsame Korrekturrelease für die zehn nach 1.1.1
aufgenommenen Punkte: Zähler-Ort/Asset, Immich-Großansicht, N-/PE-Schienen,
Home-Assistant-Livewerte, Zählerplatzierung, Asset-Typ-Prüfung für Verteilungen,
hierarchische Ortssortierung, Netzanschluss als Quelle, logische
Netzwerkschnittstellen und gerätebezogene Netzwerk-Warnungen.

## Lokal ausgeführte Prüfungen

- Python-Syntaxprüfung für Anwendung, Migrationen, Tests und Hilfsscripte;
- Syntaxprüfung aller TypeScript- und Vue-Scriptblöcke mit dem lokal
  vorhandenen TypeScript-Parser;
- vollständige Alembic-Kette gegen eine neu angelegte lokale SQLite-Datenbank:
  `clean -> 0027 -> 0028 -> 0027 -> head`;
- Prüfung, dass Revision 0028 alle neuen Spalten, Constraints, Fremdschlüssel,
  Indizes und die Tabelle `electrical_meter_placements` anlegt;
- Bestandsdatentest mit einem unter 0027 angelegten Asset, Ort und Stromzähler;
  Daten und Fremdschlüssel blieben über Upgrade, Downgrade und Re-Upgrade erhalten;
- dependency-freier Ausführungstest der hierarchischen Ortssortierung;
- statischer Abnahmecheck für alle zehn Funktionsverträge;
- Versionskonsistenz zwischen `VERSION`, Backend, Frontend und Lockdatei;
- Branding-Prüfung und dependency-freier Quellvertragstest für alle zehn
  gesammelten Punkte;
- vollständige SHA-256-Prüfung aller Manifestdateien nach erneuter Extraktion
  des finalen ZIPs.

## Ergänzte Regressionstests

- Asset-/Ortszuordnung und Ortsfallback eines Verbrauchszählers;
- Speicherung der HA-Entitäten für Gesamtleistung und Spannung;
- zwei halbe N-/PE-Bereiche und Zählerplatzierung im Zählerfeld;
- direkte Platzierung eines Assets vom Typ **Zähler**;
- Verhinderung ungültiger Verteilungs-Assets;
- Netzanschluss als Quelle und Ablehnung als Ziel;
- logische LAN-Bridge, Geräte-IP und neutrale freie Ports;
- hierarchische Sortierung von Etagen und Räumen;
- vollständiger Migrationszyklus der Revision 0028.

## Nicht lokal ausführbare Gates

Die gelieferte ZIP enthält keine installierten Python- oder Node-Abhängigkeiten.
In der strikt lokalen Umgebung waren deshalb vollständige Läufe der
SQLModel-basierten Pytest-Suite sowie von Ruff, mypy, Vue-TSC, Vite, Vitest und
vom MDI-Dateiabgleich nicht möglich. Die zugehörigen Testquellen sind enthalten
und bleiben Bestandteil des normalen Docker-/CI-Builds. Es wurden keine Pakete
oder Abhängigkeiten aus dem Internet nachgeladen.
## 1.1.1 – 2026-07-23

### Changelog

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

### Release Notes

Veröffentlicht am 23. Juli 2026.

## Behobener Fehler

Im Release 1.1.0 wurden unter **Wartung & Aufgaben** nur Zähler mit einem
expliziten monatlichen Ableseplan berücksichtigt. Bestehende Zähler, die über
die bereits vorhandene globale Regel **„Ablesung nach Tagen als fällig
markieren“** verwaltet werden, erschienen dort nicht.

DocOfHome 1.1.1 korrigiert dieses Verhalten:

- monatliche Ablesepläne funktionieren unverändert;
- Zähler ohne Monatsplan verwenden die globale X-Tage-Fälligkeit;
- Zähler ohne bisherige Ablesung sind sofort fällig;
- der Abschnitt **Ableseerinnerungen** ist auf der Wartungsseite immer sichtbar;
- bei keiner aktuellen Fälligkeit erscheint ein verständlicher Leerstatus;
- „Jetzt ablesen“ öffnet weiterhin direkt den betroffenen Zähler.

## Kompatibilität

Das Release enthält den vollständigen Stand von DocOfHome 1.1.0 einschließlich
Sprint 0038 **Photovoltaik und Energiebilanz**. Es gibt keine neue
Datenbankmigration. Der Alembic-Head bleibt `0027_energy_balance`.


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.1.1.md

Stand: 23. Juli 2026

## Umfang

Geprüft wurde das Korrekturrelease für die Ableseerinnerungen unter
**Wartung & Aufgaben** auf Basis des ausgelieferten DocOfHome-1.1.0-ZIP.

## Behobene Ursache

Die API `/api/v1/consumption/reading-reminders` übersprang Zähler ohne
monatlichen Ableseplan vollständig. Dadurch wurde die bereits vorhandene globale
Fälligkeit nach X Tagen nicht in das Wartungsmodul übernommen. Zusätzlich war
die komplette Erinnerungskarte im Frontend bei einer leeren Antwort verborgen.

## Ausgeführte lokale Prüfungen

- Python-Syntaxprüfung der geänderten Backend-, Test- und Prüfscripte;
- dependency-freier Rechentest für Zähler ohne Ablesung, überfällige
  Intervallablesung und noch nicht erreichte Fälligkeit;
- statische Prüfung, dass die Erinnerungskarte dauerhaft sichtbar ist;
- statische Prüfung der rückwärtskompatiblen globalen Intervallregel;
- Versionskonsistenz zwischen `VERSION`, Backend, Frontend und Lockdatei;
- vollständige SHA-256-Prüfung aller Manifestdateien nach erneuter Extraktion;
- Vergleich des Alembic-Heads: unverändert `0027_energy_balance`.

## Ergänzte Regressionstests

- Zähler ohne Monatsplan und mit überfälliger letzter Ablesung erscheint;
- Zähler ohne bisherige Ablesung erscheint sofort;
- noch nicht im gewählten Horizont liegende Intervallablesung erscheint nicht;
- monatlich terminierte Erinnerung verschwindet weiterhin nach einer Ablesung
  im betreffenden Zeitraum.

## Nicht ausführbare Gates

Die ZIP enthält keine installierten Python- oder Node-Abhängigkeiten. Daher
konnten vollständige Läufe von SQLModel/Pytest, Ruff, mypy, Vue-TSC, Vite und
Vitest in der strikt lokalen Umgebung nicht erneut ausgeführt werden. Die
entsprechenden Testquellen sind enthalten; diese Gates bleiben Bestandteil des
normalen Docker-/CI-Builds.
## 1.1.0 – 2026-07-23

### Changelog

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

### Release Notes

Veröffentlicht am 23. Juli 2026.

## Photovoltaik und Energiebilanz

Der neue Bereich **Verbrauch → PV & Energiebilanz** dokumentiert
Netzanschluss, Netzbetreiber, Energieversorger und Zählpunkt. Vorhandene
kumulative kWh-Zähler werden Netzbezug, PV-Erzeugung und Netzeinspeisung
zugeordnet. Daraus berechnet DocOfHome monatlich:

- Hausverbrauch;
- PV-Eigenverbrauch;
- Autarkiegrad;
- Eigenverbrauchsquote.

PV-Quellen, Wechselrichter und Speicher lassen sich einzeln erfassen und
optional mit vorhandenen Assets verbinden.

## Elektro-Topologie

Ein Ziel kann nun mehrere dokumentierte Energiequellen besitzen. Damit können
beispielsweise Netzanschluss und PV-Wechselrichter dieselbe Sammelschiene oder
Verteilung speisen. Zyklen und doppelte identische Verbindungen bleiben
verhindert. Die Oberfläche zeigt und verwaltet alle eingehenden Verbindungen.

## Verbrauch und Bedienung

- neuer Zählertyp **Netzeinspeisung**;
- eigene Diagrammskalierung je Zähler beziehungsweise Statistikserie;
- zuverlässige Dashboard-Zuordnung für Strom und Gas mit automatischer
  Übernahme der Primärmarkierung und stabilem Fallback;
- Ableseerinnerungen direkt unter **Wartung & Aufgaben**;
- visuelle Immich-Fotoauswahl im Ablesedialog.

## Kompatibilität

Das Release baut auf `1.0.0-fix2` auf und behält dessen Korrekturen vollständig
bei. Der Alembic-Head steigt von `0026` auf `0027`. Vor dem Update ist wie immer
ein vollständiges Backup des persistenten Datenordners erforderlich.

Details stehen in:

- `docs/MIGRATION_GUIDE_1.1.0.md`
- `docs/VALIDATION_REPORT_1.1.0.md`
- `docs/KNOWN_LIMITATIONS_1.1.0.md`
- `docs/sprints/0038-photovoltaic-energy-balance.md`


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.1.0.md

Stand: 23. Juli 2026  
Ausgangspaket: `DocOfHome-v1.0.0-fix2(1).zip`  
Arbeitsweise: ausschließlich lokale Dateien und lokal vorhandene Werkzeuge

## Erfolgreich ausgeführt

- Ausgangs-ZIP separat extrahiert und den 1.1.0-Stand dagegen abgeglichen;
  keine Datei des Fix2-Ausgangsstands wurde entfernt.
- Python-Syntax aller Backend-, Migrations- und Testmodule mit `compileall`
  geprüft.
- zentrale Version `1.1.0` in `VERSION`, Backend-Metadaten,
  `frontend/package.json` und `frontend/package-lock.json` geprüft.
- sichtbares Produkt-Branding mit `scripts/check-branding.py` geprüft.
- vollständige Alembic-Migrationskette `0001 -> 0027` direkt gegen eine lokale
  SQLite-Datenbank ausgeführt.
- Migration `0027` technisch auf `0026` zurückgesetzt und erneut auf `0027`
  aktualisiert.
- separaten Nutzdatentest `0026 -> 0027` ausgeführt; vorhandene Assets,
  Verbrauchszähler und Elektroverbindungen blieben erhalten.
- nach Migration `0027` einen Zähler des Typs `electricity_feed_in` sowie zwei
  verschiedene aktive Quellen auf demselben Elektro-Topologie-Ziel angelegt.
- Energiebilanz-Rechenkomponente lokal ausgeführt: Hausverbrauch,
  Eigenverbrauch, Autarkiegrad, Eigenverbrauchsquote und die Kennzeichnung
  physikalisch inkonsistenter Eingangswerte geprüft.
- Pydantic-Validierung der Energie-Konfiguration und Energiekomponenten lokal
  ausgeführt.
- eigenständig kompilierbare TypeScript-Module unter strikten Einstellungen
  geprüft.
- TypeScript-Syntax aller `.ts`-Dateien und aller Vue-`script setup`-Blöcke
  geprüft; die geänderten Vue-Skripte wurden zusätzlich mit lokalen
  Framework-Stubs streng typgeprüft.
- geänderte Vue-Dateien auf Grundstruktur und doppelte Attribute geprüft.
- Frontend-Logik für eigene Diagrammskalierung je Serie und mehrere eingehende
  Topologieverbindungen kompiliert und mit Node ausgeführt.
- gegenüber dem geprüften Fix2-Ausgangsstand keine neuen MDI-Icon-Namen
  eingeführt.
- statische Regressionen der Fix2-Funktionen geprüft: Gebäudestruktur-Assistent,
  globaler Suchfokus und `/`-Kürzel, Dashboard-Drag-and-Drop, FRITZ!Box-Hostliste
  und MAC-Zuordnung, lesbare Änderungshistorie und durchsuchbare Asset-Auswahl.
- Sprint-0038-Verträge geprüft: Einspeisezähler, Primärzählerübernahme und
  Fallback, Ableseerinnerungen, visuelle Immich-Auswahl, Energie-API,
  Mehrquellen-Topologie und Migration `0027`.
- Shell-Skripte auf Unix-Zeilenenden normalisiert und als ausführbar markiert.
- Release-ZIP nach der Erzeugung vollständig getestet, erneut extrahiert und
  gegen das interne SHA-256-Manifest geprüft.

## Im Quellstand enthaltene Regressionstests

- Energiebilanz aus Netzbezug, PV-Erzeugung und Netzeinspeisung;
- mehrere PV-Quellen, Wechselrichter und Speicher;
- Primärzählerübernahme und deterministischer Fallback für Strom und Gas;
- Mehrquellen-Topologie, Zyklus- und Doppelverbindungsverbot;
- Migrationstabellen und parallele Einspeisungen;
- eigene Statistikskalierung je Verbrauchsserie.

## In dieser lokalen Umgebung nicht vollständig ausführbar

Die gelieferte ZIP enthält weder installierte Python-Abhängigkeiten noch
`frontend/node_modules`. Lokal fehlen insbesondere `sqlmodel`, `ruff`, `mypy`,
`vue-tsc`, Vite und Vitest. Entsprechend konnten die vollständigen
Dependency-basierten Läufe `pytest`, Ruff, mypy, `npm test` und
`npm run build` nicht ausgeführt werden. Es wurden keine Pakete aus externen
Quellen nachgeladen, weil ausdrücklich ausschließlich lokal mit der ZIP
gearbeitet werden sollte.

Das finale Laufzeit-Gate auf dem Zielsystem beziehungsweise in CI bleibt:

```bash
sh scripts/check.sh
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Die lokale Prüfung deckt Syntax, fachliche Rechenlogik, reale SQLite-Migration,
Datenerhalt, zentrale Frontend-Logik, Versionskonsistenz sowie Paket- und
Manifestintegrität ab. Ein vollständiger Container-Build mit den festgelegten
Lockfile-Abhängigkeiten bleibt davon getrennt.
## 1.0.0 – 2026-07-23

### Changelog

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


### Historische Validierungsberichte

#### VALIDATION_REPORT_1.0.0.md

Datum: 23. Juli 2026

## Backend

- FastAPI-Komplettimport: bestanden (`DocOfHome API`, Version `1.0.0`)
- Ruff: bestanden
- mypy: bestanden, 108 Quelldateien
- Pytest: bestanden, 189 Tests
- frische Datenbank: bestanden
- Alembic `upgrade head` und `check`: bestanden
- Upgrade 0023 → 0026: bestanden
- Wiederanlauf von 0024 mit verwaister `_alembic_tmp_work_items`-Tabelle:
  bestanden; kanonischer Datensatz erhalten, Arbeitstabelle entfernt und
  Revision 0026 erreicht
- Downgrade 0026 → 0023 → 0026: bestanden
- neue API-/Service-, Datenintegritäts- und Connector-Tests: bestanden

## Frontend

- finales `npm ci` mit `package-lock.json`: bestanden
- MDI-Prüfung: bestanden, 205 Icons
- Vitest: bestanden, 104 Tests in 32 Dateien
- `vue-tsc --noEmit`: bestanden
- Vite-Produktionsbuild: bestanden
- Branding-Prüfung: bestanden
- iPhone-typische Breite 390 × 844: bestanden; Ablesedialog füllt den
  Viewport, Zahlenfeld verwendet `type=number`, `inputmode=decimal` und den
  zählerabhängigen `step`
- direkter SPA-Aufruf `/consumption`: bestanden

Der Produktionsbuild meldet lediglich den nicht blockierenden Hinweis auf ein
JavaScript-Hauptbundle über 500 kB. Funktion, Cachebarkeit und Kompression sind
nicht beeinträchtigt.

## Container

- Compose-Struktur: bestanden
- Healthcheck vorhanden: bestanden
- kein privilegierter Modus und kein Docker-Socket: bestanden
- FastAPI-Importschritt im Dockerfile vorhanden: bestanden
- echter Image-Build/Container-Neustart: auf dem ausführenden Windows-Host nicht
  ausführbar, da weder Docker, Podman noch WSL installiert sind

Dieser Umgebungsstatus ist kein verschleierter Testerfolg. Der Dockerfile- und
Compose-Vertrag wurde statisch und der identische Startpfad lokal mit frischem
Datenordner, Migration, Readiness, direktem SPA-Aufruf und erneutem Start gegen
den persistenten Ordner geprüft.

## Datenintegrität und Sicherheit

- globale Inventarnummern einschließlich Archivreservierung: bestanden
- Kalenderregeln über Februar, Schaltjahr und Sommerzeitgrenze: bestanden
- Ableseerinnerung verschwindet nur nach Ablesung derselben Periode: bestanden
- fehlende Vergleichswerte bleiben `null`, keine falsche Null: bestanden
- Importvorschau ohne Write, Konfliktstrategien und Rollback: bestanden
- JSON-/CSV-Export ohne Integrations-URLs, Konten oder Secrets: bestanden
- Audit redigiert sensible Felder und ist unveränderlich: bestanden
- Archive, Dokumentlinks, Wiki-Restore, Suche, VLAN-null und Nextcloud-Ordner:
  vollständige Regression bestanden

## Release-Artefakt

Das Paket wird nach Erstellung in ein frisches Verzeichnis entpackt. Ausschlüsse,
Versionskonsistenz, FastAPI-Import, Frontendbuild und SHA-256 werden erneut
geprüft; das Ergebnis steht im externen Release-Manifest.

#### VALIDATION_REPORT_1.0.0_FIX2.md

Stand: 23. Juli 2026

## Erfolgreich geprüft

- ZIP-Ausgangsstand und Projektstruktur
- Python-Syntax aller Backend-, Migrations- und Testmodule mit `compileall`
- TypeScript-Syntax und interne Typbezüge aller `.ts`-Dateien sowie aller
  `<script setup lang="ts">`-Blöcke unter den strikten Projekteinstellungen
- Vue-Templates der geänderten Oberfläche auf doppelte Attribute geprüft
- gegenüber dem geprüften 1.0.0-Ausgangsstand keine neuen MDI-Icon-Namen
  eingeführt; der vorhandene Satz von 207 Icons bleibt unverändert
- zentrale Version mit `scripts/check-version.py`
- sichtbares Branding mit `scripts/check-branding.py`
- neue beziehungsweise angepasste Regressionstests für Suchkürzel,
  Location-Routen und lesbare Audit-Kontexte
- frische Extraktion des Release-ZIPs sowie erneute Syntax-, Versions-,
  Branding- und Manifestprüfung

## In dieser isolierten Arbeitsumgebung nicht vollständig ausführbar

Der NPM-Paketproxy antwortete während der Validierung wiederholt mit HTTP 503.
Dadurch konnten `npm ci`, der echte `vue-tsc`-Lauf, Vite-Build und Vitest hier
nicht vollständig ausgeführt werden. Der Python-Paketindex stellte außerdem die
festgelegten Projektabhängigkeiten nicht bereit, weshalb Pytest, Ruff, mypy und
die Alembic-Laufzeitprüfung in dieser Umgebung nicht wiederholt werden konnten.
Eine Docker-Engine ist auf dem Prüfhost nicht installiert.

Der Docker-Build auf dem Zielsystem bleibt deshalb das finale Laufzeit-Gate:

```bash
docker compose build --no-cache
docker compose up -d
```

Die im Paket enthaltenen Prüfskripte und CI-Definitionen bleiben unverändert
verfügbar.
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

## 1.6.3 – Nachträgliche Elektro-Korrektur 2026-07-28

- Drag-and-drop von Schutzgeräten innerhalb vollständig überdeckender
  Phasen-/Kammschienen wieder zugelassen; Teilüberdeckung bleibt gesperrt.
- Allgemeine DIN-Assets unter Kammschienen mit fachlich eindeutiger Meldung
  abgewiesen.
- automatische Schienenkontakte vor der Ableitung geflusht und bei
  Topologieaufrufen selbstheilend abgeglichen.
- Archivieren für Schutzgeräte und Schrankkomponenten in der Detailansicht
  ergänzt.
- Archivierung einer Phasenschiene deaktiviert deren Einspeisung und
  automatisch erzeugte Ausgänge atomar, ohne die Schutzgeräte zu entfernen.

### 1.6.3 – Korrektur gemischter Kammschienen-Reihen

- Kammschienen können gemischte Reihen aus Schutzgeräten und allgemeinen DIN-Geräten überspannen.
- Nur Schutzgeräte erhalten automatisch abgeleitete Kontakte und Phasen.
- Fehlerhinweise beim Speichern von Schrankkomponenten werden vollständig im Dialog angezeigt.

## 1.6.3.2 – Verbindliche Kammschienen-Autoverkabelung

- sichtbare, vollständig überdeckte Schutzgeräte werden beim Speichern als
  explizit serverseitig validierte Kontaktziele übermittelt;
- direkter Fallback ergänzt den kanonischen Schutzgeräte-Repositorypfad;
- alte manuelle Einspeisungen werden vor Aktivierung des neuen Kontakts
  transaktionssicher ersetzt;
- stille Erfolgsmeldungen mit null Kontakten bei erwarteten Geräten verhindert.

### Release Notes

DocOfHome 1.0.0 ist die erste stabile Version des lokalen digitalen
Hauszwillings. Der Schwerpunkt liegt auf vollständiger technischer
Dokumentation, updatefähiger Datenhaltung und optionalen, eng begrenzten
Integrationen.

Die Version ergänzt ein konfigurierbares Dashboard, mobile
Zählerstandserfassung, Monats-/Jahresvergleiche, Kalenderwartungen,
Ableseerinnerungen, globale Inventarnummern, erweiterte Netzwerkdokumentation,
read-only FRITZ!Box-Vorschläge, logische Workloads, Datenportabilität,
Änderungshistorie und einen geführten Fachassistenten.

Vor dem Update ist ein lokales und extern gesichertes Backup erforderlich. Die
Migrationen 0024 bis 0026 werden beim Containerstart automatisch angewendet.
Die finale Paketfassung kann Migration 0024 außerdem sicher fortsetzen, wenn
ein zuvor abgebrochener SQLite-Batchlauf eine `_alembic_tmp_*`-Arbeitstabelle
hinterlassen hat; manuelle Eingriffe in die Datenbank sind dafür nicht nötig.

DocOfHome 1.0 besitzt keine Authentifizierung und darf ausschließlich in einem
vertrauenswürdigen privaten Netzwerk betrieben werden.

## Aktualisierter Fixstand

Dieser weiterhin als Version 1.0.0 geführte Stand ergänzt Verbindungstests direkt im Erst-Setup, FRITZ!Box-Unterstützung, die geführte Etagen-/Raumerfassung, Immich-Berechtigungshinweise, eine visuelle Immich-Bildauswahl, die korrigierte Home-Assistant-Geräteanzeige und ein eigenes Browser-Icon.

## Fixstand 2

Der zweite 1.0.0-Fixstand verbessert Bedienbarkeit und Nachvollziehbarkeit: Gebäudestrukturen lassen sich nach dem Erst-Setup weitergeführt bearbeiten, die globale Suche erhält einen zuverlässigen Fokus und das alternative Kürzel `/`, Dashboard-Kacheln werden direkt per Drag-and-Drop sortiert, FRITZ!Box-Geräte erscheinen im Netzwerkmodul, die Änderungshistorie zeigt verständliche Vorher-/Nachher-Werte und bestehende Assets werden im Assistenten über eine Suchliste ausgewählt.

Die Datenbankstruktur und die Produktversion bleiben unverändert.
