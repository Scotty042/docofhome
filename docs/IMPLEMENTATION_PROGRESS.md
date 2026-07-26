# DocOfHome – Implementierungsfortschritt

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
