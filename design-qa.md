# Design-QA – DocOfHome 1.9.1

Datum: 30. Oktober 2026. Product Design: Umsetzung der ausdrücklich ausgewählten Variante 1. Gegenstand ist die echte Vue-/Vuetify-Anwendung aus dem bereitgestellten 1.9.0-Quellpaket, keine isolierte Designattrappe.

## Referenz und Prüfaufbau

Ausgewählte Referenz: `docs/design-1.9.1/source-selected.png` (ursprünglich 1487 × 1058). Für den Desktopvergleich proportional auf 1440 × 1024 normalisiert. Tatsächliche Anwendung bei 1440 × 1024, DPR 1; deutscher Sprache und Zeitzone Europa/Berlin im Hauptprüflauf. Vollvergleich: `comparison-desktop.png`; Detailvergleich: `comparison-focus.png` im selben Ordner. Beide Bilder wurden gemeinsam visuell geprüft.

Lokaler Test unter 127.0.0.1:4181 mit eigenem FastAPI-Backend auf Port 4182, frischer Datenbank und ausschließlich Beispieldaten. 64 Geräte, Räume, Zähler und Aufgaben sowie Filament- und LEGO-Beispiele. Keine Verbindung zu NAS, produktiver Datenbank oder aktiven Integrationen. Chrome wurde mit frischem temporärem Kontext über Playwright ausgeführt. Der Nutzer hat diesen lokalen Prüfweg ausdrücklich genehmigt, nachdem die @Browser-Steuerung ausfiel.

## Vergleich der fünf Gestaltungsebenen

| Ebene | Ergebnis |
| --- | --- |
| Aufbau und Navigation | Salbeifarbene 274-px-Seitenleiste, Suchleiste, große Einleitung, Kennzahlen und zweispaltige Hauptkarten entsprechen der ausgewählten Richtung. Zusätzliche vorhandene Module bleiben erreichbar. |
| Typografie | Serifentitel und Zahlenhierarchie, Source Sans 3 für Bedienung/Inhalte; Schriftdateien lokal ausgeliefert. Keine externen Schriftabrufe. |
| Farben und Oberflächen | Cremefarbener Hintergrund, weiße Karten, dunkelgrüne Aktionen, dezente Trennlinien; abgestimmter Dunkelmodus erhalten. |
| Abstände und Proportionen | Hauptkarten im 7:5-Raster, einheitliche Innenabstände, ausgerichtete Filter und Listen. Auf kleinen Displays einspaltig, temporäre Navigation. |
| Inhalte, Symbole und Verhalten | Vorhandene MDI-Bibliothek; echte API-Daten und vorhandene Fachfunktionen. Keine simulierten Messwerte, Diagramme oder Statusbehauptungen. |

Bewusste daten-/funktionsbedingte Abweichungen: aktuelles Datum, echte offene Aufgaben und Verbrauchswerte; zusätzliche Dashboard-Bearbeitung und Verwaltungsgruppe. Fälligkeiten sind gruppierbar, statt alle Aufgaben künstlich auf denselben Tag zu setzen. Die Vorlage ist eine visuelle Richtung; eine pixelidentische Bildkopie wird nicht behauptet.

## Gefundene und behobene Probleme

- Unlesbare Symbole auf hellen Avatarflächen: explizite Vordergrundfarben für helle und dunkle Oberflächen. Nachweis: aktuelle Inventar- und Detailbilder.
- Navigation schloss Gruppen beim Wechsel zur Übersicht: Mehrfachöffnung und gespeicherte Gruppen pro Sitzung; aktive Route öffnet ihre Gruppe.
- Zu enge Fälligkeitskarte und gestreckte Chips: 7:5-Aufteilung und korrigierte Flexregeln. Nachweis: Desktopvergleich.
- Zu große Avatare in der mobilen Inventarliste: feste 44-px-Spalte statt wachsendem Flexelement. Nachweis: `inventory-mobile.png`.
- Zu schmale Wertespalten auf kleinen Handys: Verbrauchszeilen als zweispaltiges Raster, Vergleich darunter. Nachweis: `dashboard-390.png` und `mobile-followup.json`.
- Gleichzeitige Dashboard-Abfragen erzeugten konkurrierende Aufgaben-Synchronisierung: die beiden betroffenen Abfragen laufen nacheinander; keine Backendänderung.
- Vorhandene Home-Assistant-Abfrage verwendete unzulässiges Seitenlimit 1000: auf erlaubte 500 korrigiert, Nachladen weiterer Seiten und einmaliges Refresh durch gezielten Test geprüft.
- Erster Filtertest verwendete „Küche“ statt des dargestellten Pfads „Zuhause / Küche“: Test korrigiert; UI und URL-Filter geprüft.

Keine offenen P0/P1/P2-Designbefunde innerhalb des überarbeiteten Umfangs. P3: Abstände und Symbolvarianten weichen an einigen Stellen geringfügig von der Bildreferenz ab; die übrigen Fachmodule verwenden ihr bisheriges Seitenlayout mit dem neuen gemeinsamen Erscheinungsbild.

## Browserprüfung

`docs/design-1.9.1/browser-results.json`: 31 bestandene Prüfungen. Dashboarddaten, Inventarsuche, Rücksprung mit erhaltener Suche, Ortsfilter und Zurücksetzen, vier Detailregister, echtes Speichern und Wiederherstellen eines Gerätenamens in der Testdatenbank, mobile Hauptaktionen und Suche sowie Dunkelmodus.

Überlaufprüfungen bei 360, 390, 768, 960 und 1440 Pixeln für Dashboard, Inventar und Detailansicht. Zusätzlich bei 390 Pixeln Räume, Filament, LEGO, Netzwerk, Elektro, Verbrauch, Wartung, Wissen, Dokumente und Einstellungen. Die visuelle Kontrolle ergänzt die Überlaufprüfung, weil lesbare Wertespalten durch bloße Überlaufmessung nicht sichergestellt sind. Der gezielte mobile Nachtest prüft auch deren Mindestbreite, zusätzlich bei 599 Pixeln.

`browser-followup.json`: tatsächlich geladene mobile Inventarliste, tatsächlicher Suchtreffer und Desktop-Tastaturbedienung mit Ctrl+K und Escape nachgeprüft. Keine JavaScript-Laufzeitfehler. Zwei erwartete HTTP-409-Meldungen bleiben in der isolierten Testkonfiguration: Home Assistant deaktiviert und Nextcloud nicht eingerichtet. Diese Integrationsabläufe wurden nicht extern geprüft. Die zuvor beobachtete ungültige 422-Abfrage ist behoben; der ältere Hauptprüflauf bleibt als unveränderter Vorher-Nachweis erhalten.

## Kontrast und Bedienung

Gemessene Designfarben in `contrast.json`: heller Haupttext 13,87:1, gedämpfter Text 5,01:1, weiße Beschriftung auf Primärfarbe 7,21:1, Navigation 12,48:1. Fokusmarkierungen, beschriftete Aktionssymbole, echte Links, mobile Menüpunkte und reduzierte Bewegung berücksichtigt. Dies ist keine vollständige WCAG-Zertifizierung und kein Screenreader-Gesamtaudit.

## Technische Prüfung und Grenzen

- Vue-Typprüfung erfolgreich; Produktionsbuild erfolgreich, bestehende Warnung zum großen JavaScript-Bündel bleibt bestehen.
- 217 Frontendtests in 66 Dateien bestanden. Anschließend die drei Home-Assistant-Tests mit korrigiertem API-Limit erneut bestanden.
- 287 MDI-Symbole gültig. Versions-, Release- und Brandingprüfung bestanden.
- Frische Alembic-Migration bis 0061 erfolgreich, keine neue Migration.
- Gezielte Backendtests: 66 bestanden, ein Fremdschlüsselfehler im Test `test_asset_creation_repairs_missing_code_counter`. Mit unverändertem 1.9.0 reproduziert; beide Protokolle liegen bei. Kein vollständiger grüner Gesamtprüflauf behauptet.
- Backend-Anwendung, Migrationen und Containerkonfiguration unverändert gegenüber dem Original; keine ursprüngliche Quelldatei fehlt. Siehe `source-integrity.json`.
- Testbackend unter Python 3.12; Dockerbuild und Python 3.13 nicht geprüft. Reale Cloud-/NAS-/Druckerintegrationen und Migration produktiver Bestandsdaten nicht geprüft.

**Final result: passed** – für das visuelle Redesign und die beschriebenen lokalen Kernabläufe. Die produktive Installation blieb unverändert; die vollständige Releasefreigabe bleibt aufgrund der ausdrücklich genannten Prüfgrenzen offen (`full_quality_gate_passed: false`).
