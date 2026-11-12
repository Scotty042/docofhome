# Prüfung 1.10.1 – Verlauf und Zeitkorrekturen – 12. November 2026

- 229 Frontendtests in 68 Dateien bestanden. Vue-Typprüfung, Produktionsbuild und Prüfung aller 289 MDI-Symbole bestanden; bekannte Bundlegrößenwarnung.
- 22 gezielte Backendtests bestanden: Start/Pause/Ende, Wiederaufnahme, manuelle Zeiten, Änderungen mit stabiler ID, Überschneidungen, angrenzende Intervalle, ungültige/future/zeitzonenlose Eingaben, Schutz laufender Timer, MCP-Berechtigungen, beide Authentifizierungswege, Sommer-/Winterzeit, Export/Backup-Regression und Modulstandard bei Neuinstallation.
- Neue/geänderte Zeiterfassungsdateien und MCP-Server bestehen Ruff. Mypy weiterhin 80 Bestandsmeldungen in 15 Dateien; keine neue Diagnose gegenüber 1.10.0.
- Lokale Browserprüfung mit isoliertem Testbestand und Produktionsbundle: 30-Tage-Vorauswahl, Von/Bis-Felder, chronologischer Verlauf, Ticketsummen, Bearbeitungsdialog, gespeicherte Infoänderung und manueller Dialog geprüft. Keine Änderung produktiver Daten. Automatisierte API-Tests prüfen die Zeitkorrektur und Neuberechnung.
- Keine neue Migration; Head 0062. Kein erneuter vollständiger Backend-Gesamtlauf; die offenen Gesamtprüfgrenzen aus 1.10.0 gelten weiter. Kein Docker-/Linux-/Python-3.13-Build. Kein GitHub-Push/Release.
- ZIP folgt dem Publisher-Vertrag: VERSION und Dockerfile direkt auf oberster Ebene, keine lokalen Abhängigkeiten, Datenbanken, Secrets oder Cacheverzeichnisse. Jede enthaltene Datei wird nach Paketbau byteweise geprüft; SHA-256 wird neu erzeugt.

---

# Prüfung 1.10.0 – Zeiterfassung – 12. November 2026

Paketkorrektur: ZIP enthält die Quellen direkt auf oberster Ebene, insbesondere `VERSION`, `Dockerfile`, `compose.yaml` und `.github/`. Der zusätzliche Versionsordner wurde entfernt. Der Paketbau prüft diese Publisher-Vorgabe künftig automatisch.


- 226 Frontendtests in 68 Dateien bestanden; Typprüfung, Produktionsbuild und Symbolprüfung erfolgreich (bestehende Bundlegrößenwarnung).
- 25 gezielte Backendtests bestanden: Zeiterfassung, MCP-Lesen/Schreiben/Berechtigungen, beide Authentifizierungswege, Wiederaufnahme, Export, Backup-/Transportregression und Sommer-/Winterzeit.
- Migration 0062 auf frischer Datenbank sowie Upgrade/Downgrade/Wiederupgrade mit gezielter Modulauswahl erfolgreich; eindeutiger aktiver Timer geprüft.
- Neue Backenddateien und MCP-Server: Ruff bestanden. Ruff gesamt: 110 Meldungen. Davon 103 wie Basis 1.9.2 plus sieben aus unverändert übernommenen Filamentdateien aus 1.9.3.
- Mypy: 80 Meldungen in 15 Dateien; Vergleich mit Basis 1.9.2 in derselben Umgebung ergibt dieselben Diagnosemeldungen. Keine neue Meldung für die Zeiterfassung.
- Erster Backend-Gesamtlauf: 333 bestanden, 33 fehlgeschlagen, 72 Warnungen (366 Tests). Drei Migrationsprüfungen erwarteten noch Head 0061; Erwartungen auf 0062 und neues Modul angepasst und anschließend separat erfolgreich geprüft. Die drei später ergänzten MCP-Tests sind im grünen gezielten 25-Test-Lauf enthalten. Kein abschließender vollständiger grüner Gesamtprüflauf behauptet.
- Die übrigen 30 fehlgeschlagenen Fälle betreffen bestehende Bereiche (Elektro, Datenmigrationen, Asset-Zähler, Netzwerk, HA und Kalenderlogik); sie wurden in diesem Release nicht behoben. Die vollständige Liste des ersten Laufs folgt.
- Lokale Umgebung: Python 3.12, Node 24; Projektziel Docker/Python 3.13 und Node 22 nicht ausgeführt. Kein Docker installiert. Kein produktives Update, kein GitHub-Push/Release.
- Handbuch und MCP-Dokumentation aktualisiert; Historie und Manifest bleiben zentral in PROJECT_HISTORY.md.

### Fehlgeschlagene Tests des ersten Gesamtlaufs

- `tests/test_asset_engine.py::test_asset_creation_repairs_missing_code_counter`
- `tests/test_collected_integration_migration.py::test_collected_integration_migration_upgrade_downgrade_and_reupgrade`
- `tests/test_docker_multi_host_ssh.py::test_migration_copies_legacy_socket_configuration`
- `tests/test_electrical_circuit_asset_migration.py::test_circuit_asset_migration_preserves_existing_data_and_downgrades`
- `tests/test_electrical_circuit_migration.py::test_circuit_migration_preserves_electrical_data_and_downgrades`
- `tests/test_electrical_circuits.py::test_circuit_asset_assignments_are_searchable_and_historic`
- `tests/test_electrical_layout.py::test_meter_asset_can_be_placed_without_consumption_meter`
- `tests/test_electrical_layout.py::test_phase_rail_contacts_every_fully_covered_din_device`
- `tests/test_electrical_layout.py::test_structured_phase_rail_replaces_manual_feeds_and_contacts_all_din_devices`
- `tests/test_electrical_layout.py::test_phase_rail_can_link_to_rcd_din_asset`
- `tests/test_electrical_migration.py::test_electrical_migration_preserves_existing_data_and_is_downgrade_safe`
- `tests/test_electrical_migration.py::test_electrical_migration_upgrades_a_fresh_database_without_drift`
- `tests/test_electrical_review_fixes.py::test_distribution_capacity_cannot_exclude_active_device`
- `tests/test_electrical_topology.py::test_supply_topology_paths_phases_cable_and_rcd_counts`
- `tests/test_electrical_topology.py::test_archived_endpoints_cannot_receive_new_connections`
- `tests/test_electrical_topology.py::test_grid_connection_is_a_real_source_only_endpoint`
- `tests/test_electrical_topology.py::test_cabinet_component_accepts_multiple_feeds_and_preserves_phases`
- `tests/test_electrical_topology.py::test_phase_rail_phase_is_forced_when_wiring_a_protective_device`
- `tests/test_electrical_topology.py::test_n_and_pe_rails_are_selectable_and_keep_auxiliary_conductors_separate`
- `tests/test_electrical_topology.py::test_separate_neutral_feed_does_not_inherit_parallel_line_phases`
- `tests/test_electrical_topology_migration.py::test_topology_migration_preserves_existing_data_and_downgrades`
- `tests/test_filament.py::test_migration_upgrade_downgrade_and_module_choices`
- `tests/test_home_assistant.py::test_parallel_home_assistant_reads_share_one_sync`
- `tests/test_home_assistant_selection_migration.py::test_selection_migration_preserves_links_and_downgrades_to_0010`
- `tests/test_immich_album_selection_migration.py::test_immich_album_selection_migration_preserves_integration_and_downgrades`
- `tests/test_immich_migration.py::test_immich_link_migration_preserves_existing_data_and_downgrades`
- `tests/test_lego_collection.py::test_migration_keeps_existing_module_choices_and_supports_downgrade`
- `tests/test_network.py::test_release_1_7_ip_reconciliation_keeps_documented_address`
- `tests/test_nextcloud_document_root_migration.py::test_document_root_migration_preserves_nextcloud_configuration_and_downgrades`
- `tests/test_recipe_title_migration.py::test_upgrade_repairs_blank_titles_without_losing_recipe_content`
- `tests/test_release_data_integrity.py::test_calendar_recurrence_uses_last_available_february_day`
- `tests/test_release_migration_recovery.py::test_release_migration_recovers_stale_sqlite_batch_table`
- `tests/test_subdistribution_layout_migration.py::test_0030_allows_subdistribution_sections_and_round_trips`

---

# Prüfung 1.9.3 – AMS und Store-Bilder

- 223 Frontendtests und 16 gezielte Filament-Backendtests bestanden.
- Vue-Typprüfung, Produktionsbuild, 289 MDI-Symbole sowie Versions- und Releaseprüfung erfolgreich.
- Neue AMS-Anzeige und gemeinsame Bildübernahme mit ausschließlich lokalen Testantworten geprüft.
- Zwei echte öffentliche Store-Abgleiche in einer isolierten Testdatenbank erfolgreich: A00-P6 → Magenta (10202), Hellgrau (10104) → angefragtes Originalbild.
- Keine Änderung produktiver Daten oder Einstellungen, keine neue Migration. Kein neuer vollständiger Backend-/Docker-Prüflauf; bestehende Prüfgrenzen weiter gültig. Details in `design-qa.md`.

---

# Prüfung der kompakten Oberfläche 1.9.2 – 30. Oktober 2026

- Separate lokale Testinstanz und Vorher-Nachher-Vergleich; keine Änderung der NAS-Installation.
- Kompakte Titel, Navigation, Tabellen, Formulare und Karten; mobile Schaltflächen weiterhin mit großen Touchflächen.
- Vue-Typprüfung, Produktionsbuild, 217 Frontendtests, MDI-, Versions-, Release- und Brandingprüfung erfolgreich.
- 31 lokale Browserprüfungen erfolgreich; zusätzliche Dichte-, Mobil- und Einstellungsprüfungen in `design-qa.md` dokumentiert.
- Backend, Migrationen und Containerkonfiguration unverändert gegenüber 1.9.1. Kein neuer Backend-Gesamtprüflauf oder Dockerbuild. Die folgenden bekannten Prüfgrenzen gelten weiter.

---

# Prüfung des Redesigns 1.9.1 – 30. Oktober 2026

- Getrennte lokale Testinstanz; produktive Docker-/NAS-Installation unverändert.
- Vue-Typprüfung, Vite-Produktionsbuild, 217 Frontendtests und Prüfung von 287 verwendeten MDI-Symbolen erfolgreich.
- Frische Testdatenbank erfolgreich bis Migration 0061 aufgebaut. Keine neue Migration eingeführt.
- Gezielte Backendtests: 66 bestanden, ein Fehler in `test_asset_creation_repairs_missing_code_counter` (FOREIGN KEY constraint). Derselbe Test scheitert mit unveränderten Quellen aus 1.9.0 in derselben Umgebung.
- Backend-Anwendung und Migrationsdateien bytegleich mit dem Ausgangspaket. Lokale Python-Version 3.12; Dockerbuild/Python 3.13 nicht geprüft.
- Browser- und Designprüfung separat in `design-qa.md` dokumentiert. Kein vollständiger grüner Gesamtprüflauf behauptet.

---

# DocOfHome – aktueller Audit- und Qualitätsstatus

Stand: 29. Oktober 2026 · Release: 1.9.0 · Alembic-Head: `0061`

## Ergänzung 1.9.0

Exakte Basis ist 1.8.0 mit ZIP-SHA256
`a7c79b57268b9f8066a2d3959ebf2101e8a022eb625545e29a2b6fe39057a5d9`.
Alle 715 Basisdateien wurden vor dem Paketbau erneut gegen das Manifest geprüft.
Keine bestehende Quelldatei entfernt; 15 neue Quelldateien. Keine produktive
Installation geändert, keine echte Cloud-Anmeldung ausgeführt und kein Release
auf GitHub veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Filament/Push/LEGO/MCP/Backup/Docker/Updates gezielt | 59 bestanden, 16 Warnungen |
| Abschließender Backend-Gesamtlauf | 332 bestanden, 30 fehlgeschlagen, 71 Warnungen; exakt dieselben 30 fehlgeschlagenen Testfälle wie in 1.8.0 |
| Frontend | 209 Tests in 63 Dateien bestanden |
| Vue-/TypeScript-Typprüfung | bestanden |
| Produktionsbuild | bestanden; bestehende Bundlegrößenwarnung |
| Icons | alle 274 verfügbar |
| Release-/Branding-/Versions-/Migrationsskripte | 38 bestanden |
| TypeScript-/Vue-Syntax | 214 Skripteinheiten bestanden |
| Neue Filament-Dateien: Ruff | bestanden |
| Ruff gesamt | unverändert 103 bestehende Meldungen |
| Mypy gesamt | unverändert 60 Meldungen in 15 Dateien; keine neuen Filament-Meldungen |
| Migration | frische Datenbank bis 0061, 0060 → 0061 → 0060 → 0061 und Erhalt bestehender Modulentscheidungen geprüft |
| Schemaabgleich | vorhandene Altabweichungen; keine Filament-Abweichung |
| Etiketten | PDF mit zwei Seiten, physisch 40 × 30 mm; JPG 300 dpi; QR aus JPG und beiden gerenderten PDF-Seiten decodiert; beide PDF-Seiten visuell geprüft |
| Öffentliche Bambu-Shop-Bildsuche | reales PLA-Basic-Farbbild 10502 eindeutig gefunden und lokal gespeichert |
| Browser-Sichtprüfung | Produktionsbundle mit isoliertem Testbestand; Übersicht, Editor, sticky Buttons und Abbruch bei ungespeicherten Eingaben geprüft |
| Docker/Linux/Python 3.13, echtes Bambu-Konto/AMS, physischer M110-Druck | lokal nicht verfügbar bzw. ohne Zugangsdaten; nicht ausgeführt |

Der erste Gesamtlauf enthielt 331 bestandene Tests und 31 Fehler. Davon sind 30
identisch zum dokumentierten 1.8.0-Lauf. Die zusätzliche LEGO-Testabweichung war
eine veraltete Erwartung an die Modulliste ohne das neue Filament-Modul; diese
Erwartung wurde auf den neuen Head aktualisiert und die Upgrade-/Downgrade-Prüfung
erneut erfolgreich ausgeführt. Der abschließende Gesamtlauf bestätigt 332 bestandene
Tests und dieselben 30 Altfehler wie in 1.8.0; keine zusätzlichen fehlgeschlagenen
Testfälle. Die Gesamtprüfung ist wegen der Altfehler weiterhin nicht grün.

Die 14 neuen Backendtests prüfen unter anderem beliebige Hersteller, kombinierte
Filter und RFID-Suche, lokale Archividentität, unvollständige und wiederholte
Cloud-Seiten, Login mit Bestätigungscode, genaue Cloud-Löschanfrage, maskierte
Fehlermeldungen, MQTT-TLS und Status-Topics für mehrere Drucker, exakte RFID-
Zuordnung, unbekannte/manuelle Slots und Teilmeldungen. Echte MCP-Aufrufe prüfen
teilweise Änderungen, Schreibschutz, Archiv und Etiketten-Download. JSON-/CSV-
Übernahme, Dublettenerkennung und vollständige Wiederherstellung werden ebenfalls
gegen isolierte Datenbanken ausgeführt. Der wiederholte MCP-Lebenszyklustest
bestätigt 49 registrierte Werkzeuge; Bearer- und Token-Pfad sind weiter abgedeckt.

Die Cloud-/MQTT-Tests verwenden kontrollierte Antworten und Protokoll-Gegenstellen;
sie bestätigen keinen erfolgreichen Zugriff auf das tatsächliche Konto oder den
Drucker. Bambu verwendet nicht als stabil zugesicherte Schnittstellen. Die reale
Einrichtung ist nach Installation zu prüfen. AMS-Erkennung ist kein Nachweis einer
Drucknutzung, unvollständige Bestände bleiben gekennzeichnet. Lokales Archivieren
ist unabhängig von einer optionalen Cloud-Löschung; Cloud-Zugangsdaten fehlen in
JSON/CSV, sind jedoch in vollständigen Backups enthalten.

Lokale Laufzeit: Python 3.12.14 und Node 24.19.0. Die Zielumgebung verlangt Python
3.13 und nutzt Node 22.16.0. Backend-Entwicklungsabhängigkeiten aus 1.8.0 wurden
über eine isolierte virtuelle Umgebung wiederverwendet und um reportlab, qrcode,
paho-mqtt sowie PDF-/QR-Prüfwerkzeuge ergänzt. Das Frontend-Lockfile wurde nur in
den Versionsfeldern geändert. Prüflogs liegen neben der ZIP unter `validation-1.9.0`.

## Ergänzung 1.8.0

Basis ist der ausgelieferte und vom Nutzer installierte Stand 1.7.20, SHA256
`5458e47103b27fa1711122fcb344c4936dcb2d6514097eeb6e494706d1e40c95`.
Der Paketbau prüft jeden Basispfad gegen dessen vorhandenes Dateimanifest.
Keine vorhandene Quelldatei wird entfernt. Es wurde keine produktive Installation
geändert und kein GitHub-Release veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte Push-/LEGO-/MCP-/Backup-/Docker-/Migrationstests | 46 bestanden |
| Backend-Gesamtlauf | 318 bestanden, 30 fehlgeschlagen, 67 Warnungen (348 Tests) |
| Frontend-Gesamttests | 202 bestanden in 62 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Frontend-Produktionsbuild | bestanden; bestehende Bundlegrößenwarnung |
| Icon-Prüfung | 274 Icons verfügbar |
| Release-/Versions-/Branding-/Migrationsskripte | 38 bestanden |
| TypeScript-/Vue-Syntaxprüfung | 210 Skripteinheiten bestanden |
| Neue Push-Dateien: Ruff | bestanden |
| Ruff gesamt | 103 bestehende Meldungen |
| Mypy gesamt | 60 bestehende Meldungen in 15 Dateien; keine neuen Push-Meldungen |
| Frische Migration bis 0060 und 0059 → 0060 → 0059 → 0060 | bestanden |
| Schemaabgleich | bestehende Altabweichungen, keine Push-Abweichung |
| Docker-Image-Build und reale Smartphonezustellung | lokal nicht verfügbar, nicht ausgeführt |

Die Push-Tests verwenden die tatsächlichen HTTP-Clients mit isolierten
Serverantworten: Pushover-Formulardaten, ntfy-JSON und Bearer-Token, Unicode,
Entwurfstest ohne Speichern, tägliche Zusammenfassung für beide Dienste,
persistente Dublettenvermeidung über mehrere Sitzungen, abgelaufene Versandclaims,
unabhängige Fehler und maximal drei Versuche, Sommer-/Winterzeit, begrenzte
Nachrichtenlänge, ungültige Antworten und unterbundene Redirects.

Die Auswahl prüft bestehende monatliche Ableseregeln einschließlich erledigter
Ablesung, getrennte Kategorien, Ausschluss erledigter/archivierter Einträge und
keine doppelte Meldung automatisch erzeugter Zähleraufgaben. Backup und Restore
erhalten Konfiguration, Schlüssel und Versandmarker. Datenexporte enthalten weder
Schlüssel noch private Topics; auch Audit-Ereignisse maskieren geheime Systemwerte.
Diese Maskierung wurde beim neuen Exporttest ergänzt. Validierungsantworten der
neuen Einstellungs-API enthalten keine geheimen Eingabewerte.

Die neuen Oberflächentests führen das echte Seitenskript mit Vue-Reaktivität und
isolierten Antworten aus. Sie prüfen Entwurfstest, Speichern, Entfernen von
Schlüsseln, fehlerhaftes Speichern, Verwerfen und Schutz beim Verlassen/Neuladen.
Dies ersetzt keinen Browser-End-to-End-Test.

Automatischer Versand ist nach dem Update standardmäßig ausgeschaltet. Es wurden
keine echten Pushover-/ntfy-Nachrichten gesendet und keine Benutzerzugangsdaten
verwendet. Die Einrichtung erfordert einen Test des Empfangs auf dem eigenen
Smartphone. Ein angenommener API-Aufruf bestätigt keine Geräte-Zustellung; bei
unklarem Netzwerkergebnis ist trotz Versandmarkern eine Wiederholung möglich.

Die vollständige Qualitätsprüfung bleibt wegen der dokumentierten Altfehler
nicht grün. Die Protokolle liegen neben dem Paket unter validation-1.8.0.
Die Fehlernamen wurden mit den gespeicherten Läufen verglichen: Gegenüber
1.7.20 kommt ausschließlich der bereits in 1.7.19 dokumentierte datumsabhängige
Monatsregeltest hinzu. Er erwartet fest den 15. des aktuellen Monats, der am
29. Oktober bereits vergangen ist. Gegenüber der Fehlerliste von 1.7.19 gibt
es keinen neuen Fehlernamen. Die übrigen 29 Altfehler bleiben unverändert.

## Ergänzung 1.7.20

Basis ist der unveränderte Quellstand 1.7.19 mit SHA256
`339880ec0964b451ca188da5cc4fa08d97502fccf34369086d16487b5a8c40c2`.
Neu ist die LEGO-Sammlung. Alle bestehenden Quelldateien bleiben im Paket;
Manifest und Prüfsumme weisen Ergänzungen und Änderungen einzeln aus.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte LEGO-/MCP-/Backup-/Docker-/Migrationstests | 28 bestanden |
| Backend-Gesamtlauf | 301 bestanden, 29 fehlgeschlagen, 64 Warnungen (330 Tests) |
| Frontend-Gesamtlauf | 197 bestanden in 61 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Frontend-Produktionsbuild | bestanden; bekannte Bundlegrößenwarnung bleibt |
| Icon-Prüfung | 271 Icons verfügbar |
| Release-/Versions-/Branding-/Migrationsskripte | 38 bestanden |
| TypeScript-/Vue-Syntaxprüfung | 206 Skripteinheiten bestanden |
| Neue LEGO-Dateien: Ruff | bestanden |
| Ruff gesamt | 103 bestehende Meldungen |
| Mypy gesamt | 60 bestehende Meldungen in 15 Dateien, keine LEGO-Meldungen |
| Frische Datenbankmigration bis 0059 | bestanden |
| 0058 → 0059 → 0058 → 0059 mit vorhandenen Menüentscheidungen | bestanden |
| Schemaabgleich | bekannte Altabweichungen; keine LEGO-/Docker-Abweichung |
| Docker-Image-Build | lokal kein Docker verfügbar, nicht ausgeführt |

Die 29 fehlgeschlagenen Tests wurden anhand ihrer Namen mit dem gespeicherten
1.7.19-Gesamtlauf verglichen: kein neuer Fehler. Der seinerzeit zusätzlich
datumsabhängig fehlgeschlagene Monatsregeltest besteht am 5. Oktober.
Die vollständige Qualitätsprüfung ist damit weiterhin nicht grün. Die alten
Elektro-, Netzwerk-, Integrations- und Downgradefehler wurden nicht übersprungen.

Die neuen Backendtests prüfen normalisierte eindeutige Setnummern, exakte
Preiswerte, unbekannte gegenüber bekannten Nullwerten, ungültige Eingaben,
vollständige Seitennavigation, REST-Erstellen/Ändern/Löschen, echte MCP-Aufrufe
über Bearer und Tokenpfad, Schreibschutz und Erhalt nicht übergebener Felder.
JSON- und CSV-Roundtrips, Setnummerkonflikte bei anderer ID sowie vollständige
Sicherung/Wiederherstellung einschließlich lokalem Bild wurden ausgeführt.
Die Oberflächentests führen das tatsächliche Seitenskript mit Vue-Reaktivität
aus und prüfen Filter, unbekannte Werte und Schutz vor ungespeicherten Änderungen.
Dies ist kein Browser-End-to-End-Test.

Online-Kataloge werden von DocOfHome nicht automatisch abgefragt. Ein verbundener
Assistent kann recherchierte Angaben über MCP mit Quelle und Datum eintragen.
Verfügbarkeit und Verlässlichkeit der externen Angaben wurden hier nicht geprüft.
Es wurde keine produktive Installation geändert und kein GitHub-Release erstellt.
Der geprüfte Quellstand ist vor dem Einsatz im Ziel-Dockerimage zu testen.

## Ergänzung 1.7.19

1.7.19 baut unverändert auf dem bereitgestellten und praktisch getesteten 1.7.18-Stand auf.
Neu geprüft werden Mehrhost-Trennung, SSH-Befehlsbeschränkung, Host-Key-Pinning,
Migration einer vorhandenen Socket-Konfiguration und Sicherung der SSH-Schlüssel.
Es wurde keine produktive Installation verändert und kein GitHub-Release veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte Backendtests für 1.7.18/1.7.19 und Migrationen | 14 bestanden |
| Backend-Gesamttests | 286 bestanden, 30 fehlgeschlagen, keine Testaufbaufehler (316 Tests) |
| Frontend-Gesamttests | 192 bestanden in 60 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Frontend-Produktionsbuild | bestanden; Warnung wegen großem Hauptbundle bleibt |
| Icon-Prüfung | 270 Icons verfügbar |
| Release-, Versions- und statische Migrationsprüfungen | 38 Python-Prüfskripte bestanden |
| TypeScript-/Vue-Syntaxprüfung | 202 Skripteinheiten bestanden |
| Geänderte Backenddateien: Ruff | bestanden |
| Geänderte SSH-/Docker-Backenddateien: Mypy | bestanden |
| Ruff gesamt | 103 bestehende Meldungen verbleiben |
| Mypy gesamt | 60 Meldungen in 15 Dateien verbleiben |
| Frische Datenbankmigration bis 0058 | bestanden |
| Alembic-Schemaabgleich | nicht bestanden; ausschließlich bereits dokumentierte Altabweichungen, keine neue Docker-Host-Abweichung |
| Docker-Image und realer SSH-Zielserver | lokal nicht verfügbar, daher nicht ausgeführt |

Die neuen Tests prüfen zwei Hosts mit identischem Containernamen und identischer
Container-ID, getrennte Zuordnung zum jeweiligen Asset, Ed25519-Erzeugung und
Dateirechte, festes `known_hosts`, ausschließlich Public-Key-Anmeldung, Migration
der alten Socket-Konfiguration sowie den erzwungenen Serverbefehl. Der Helfer darf
nur `/version` und `/containers/json?all=1` abfragen. Backup und Restore wurden
einschließlich privater SSH-Schlüssel und der Rechte `0700`/`0600` geprüft.

Der Gesamtprüflauf ist weiterhin nicht grün. 29 Fehler entsprechen den bereits für
1.7.18 dokumentierten älteren Elektro-, Netzwerk-, Integrations- und
Downgrade-Prüfungen. Zusätzlich ist am Testdatum 17. September ein bestehender
Wiederholungsregeltest datumsabhängig fehlgeschlagen, weil er fest den bereits
vergangenen 15. des Monats erwartet. Keiner dieser Fehler betrifft die neuen
Mehrhost-/SSH-Tests. Sie wurden nicht übersprungen oder als bestanden dargestellt.

Die lokale Laufzeit nutzt Python 3.12.14 und Node 24.19.0. Das Zielimage sieht
Python 3.13.5 und Node 22.16 vor. Weder Docker noch ein erreichbarer SSH-Testserver
standen lokal zur Verfügung. Deshalb müssen Image-Build, Public-Key-Einrichtung,
Fingerabdruckvergleich und der erste echte NUC-Abgleich in einer isolierten
Testinstallation bestätigt werden.

## Historischer Prüfstatus 1.7.18

Stand: 8. September 2026 · Release: 1.7.18 · Alembic-Head: `0057`

## Lokaler Prüfstatus 1.7.18

**Das ZIP ist ein lokal gebauter Patch-Stand, keine vollständig grüne Produktionsfreigabe.**
Vor Einsatz in der laufenden Installation einen vollständigen externen Datenordner-Backup
erstellen und das Update zunächst in einer Testinstallation prüfen.

Basis ist unverändert die bereitgestellte 1.7.17-ZIP, SHA256
`7a50ebc3626d441dbf69cd0dd89d1adcbeb0ac0f1ac1e04483df33b94fd623b4`.
Die Release-Historie beschreibt Umfang und Kompatibilität. Das separate Dateimanifest
enthält den Vergleich jedes Quellpfads und die Prüfsumme jeder enthaltenen Datei.
Es wurde weder auf die produktive Installation zugegriffen noch ein Git-Tag veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte Backend-Regressionssuite | 47 bestanden |
| Backend-Gesamttests | 282 bestanden, 29 fehlgeschlagen, keine Testaufbaufehler (311 Tests) |
| Frontend-Gesamttests | 191 bestanden in 59 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Produktionsbuild | bestanden; Warnung wegen großem Hauptbundle bleibt |
| Icon-Prüfung | 269 Icons verfügbar |
| TypeScript-/Vue-Syntaxprüfung | 201 Skripteinheiten bestanden; nutzt jetzt lokale Lockfile-Abhängigkeit |
| Release-/Versions-/Branding-/Migrationsskripte | alle 37 Python-Prüfskripte bestanden |
| Frische Datenbank bis Migration 0057 | bestanden |
| 0056 → 0057 mit ungültigem Altrezept, Rückmigration | bestanden; Zutaten und Schritte erhalten; SQLite-Integrität und Fremdschlüssel geprüft |
| Ruff für geänderte Backend-Implementierungen und neue Tests | bestanden |
| Ruff gesamt | 112 Meldungen verbleiben; vorher 217 |
| Mypy gesamt | 65 Meldungen in 16 Dateien; vorher 66 in 17 Dateien |
| Datenbankschemaabgleich | nicht bestanden; bestehende Index-, Fremdschlüssel- und Typabweichungen bleiben |
| Docker-/Linux-/Python-3.13-Build | lokal nicht verfügbar, nicht geprüft |

Die gezielten Tests führen echte MCP-Aufrufe gegen isolierte Testinstanzen aus:
36 registrierte Werkzeuge, mehrfacher Serverstart, ungültige Tokens, Schreibschutz,
Rezept-Speichern per Bearer und Suche per Token-Pfad, Profil-/Tätigkeitsdatenerhalt,
leere Rezeptliste und 101 Rezepte über mehrere Seiten. Ferner wurden eine Sicherung
mit lokalem Rezeptbild und Zeitplan in ein frisches Datenverzeichnis zurückgespielt,
Format 1 eingelesen, manipulierte Archive zurückgewiesen und Export/Import mit
binärem Historienanhang sowie Paperless-Verknüpfung verglichen. Die Frontendtests
führen das tatsächliche Einstellungs-Skript mit Vue-Reaktivität und isolierten
Netzwerkantworten aus. Clipboard verwendet nachgebildete Browserfunktionen;
dies ersetzt keinen End-to-End-Test auf einem realen Mobilbrowser.

Laufzeit: Python 3.12.14, MCP 2.0.1, FastAPI 0.116.2, SQLModel 0.0.42,
Node 24.19.0. Vorhandene lokale Entwicklungsabhängigkeiten wurden wiederverwendet.
Das Frontend-Lockfile wurde ausschließlich in den Versionsfeldern geändert.
Das Projekt verlangt Python 3.13; CI nutzt Node 22.16. Diese Zielumgebung
muss die lokalen Prüfungen noch bestätigen.

Die Gesamtprüfung ist weiterhin nicht grün: Ältere Upgrade-/Downgrade-Ketten
stoßen auf Fremdschlüsselverletzungen, Elektrotests verwenden teils überholte
Modelle oder erwarten frühere Beschriftungen. Daneben bleiben Fehler in
Netzwerk-, Home-Assistant- und Wiederholungsregel-Tests. Diese wurden nicht
pauschal übersprungen oder durch Abschalten von Prüfungen verdeckt.
Die vormals 105 Testaufbaufehler durch den globalen MCP-Lebenszyklus treten
nicht mehr auf; dadurch laufen zusätzliche Tests erstmals bis zu ihren
fachlichen Prüfungen. Weniger Testaufbaufehler bedeutet deshalb nicht
automatisch eine vollständig fehlerfreie Anwendung.

Der Schemaabgleich meldet weiterhin Unterschiede bei Home-Assistant-Linkindizes,
`network_interfaces.is_primary` und Smart-Meter-Indizes, `ON DELETE CASCADE`
sowie dem Typ der Notizspalte. Migration 0057 ändert diese Altbereiche nicht.
Weitergehende Zugriffskontrolle der REST-API und Ladezeitoptimierung sind
nicht Teil dieses Patches. Details zu den ausgeführten Prüfungen liegen
neben der ZIP im Ordner `validation-1.7.18`.

## Historische Auditnotizen bis 1.7.1

Stand: 28. Juli 2026
Release: 1.7.1
Alembic-Head: `0048`

## Einordnung

1.6.3.8 korrigiert die FI/RCD-Gruppenzuordnung für das seit 1.6.3.7 verbindliche
DIN-Asset-Modell. Das Auswahlfeld an Phasen-/Kammschienen und N-Schienen nutzte
noch ausschließlich historische `electrical_protective_devices`. Daher waren als
DIN-Assets platzierte FI-Schutzschalter nicht auswählbar.

## Integritätsregeln

- aktuelle FI/RCD und FI/LS werden als DIN-Assets derselben Verteilung angeboten;
- historische FI/RCD-Schutzgeräte bleiben rückwärtskompatibel;
- eine Schrankkomponente referenziert entweder einen historischen FI/RCD oder ein
  FI/RCD-Asset, niemals beide;
- nur aktive, platzierte Assets mit passendem FI/RCD-Asset-Typ sind zulässig;
- ein referenziertes FI/RCD-Asset kann erst nach dem Lösen der Zuordnung aus dem
  Verteilerschrank entfernt werden;
- vorhandene Kammschienen- und DIN-Kontaktlogik bleibt unverändert.

## Qualitätsnachweis

Ausgeführt wurden Versions-, Branding-, Elektro-, Kammschienen-, Python- und
TypeScript-/Vue-Syntaxprüfungen sowie sämtliche Migrationsprüfungen bis `0047`.
Der vollständige Pytest-, Ruff-, Mypy-, Vite- und Docker-Lauf benötigt die externen
Projektabhängigkeiten und ist auf dem Zielsystem auszuführen.


## Ergänzung 1.7.1

Der Abgleich gegen 1.7.0 hat einen fachlichen Modellkonflikt aufgelöst:
Stromkreise referenzierten dort ausschließlich historische Schutzgeräte,
während seit 1.6.3.7 neue Geräte als DIN-Assets angelegt werden. 1.7.1
unterstützt beide Referenzarten mit gegenseitigem Ausschluss und serverseitiger
Validierung. Eigenständige FI/RCD bleiben als Gruppen-Schutzgeräte von der
Zuordnung zu einem einzelnen Stromkreis ausgeschlossen.
