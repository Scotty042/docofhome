# Design-QA – kompakte Oberfläche 1.9.2

Datum: 30. Oktober 2026. Grundlage ist Variante 1 aus 1.9.1. Der Nutzer wünscht ausdrücklich weniger Platzbedarf; die ursprünglichen Abstände und Schriftgrößen sind deshalb kein unveränderlicher Zielwert mehr. Farbwelt, Schriftfamilien, Gliederung und echte Funktionen bleiben bestehen.

## Aufbau und Referenzen

Zwei getrennte lokale Testversionen mit denselben Ausgangsbeispieldaten: 1.9.1 auf Port 4181, 1.9.2 auf Port 4183. Keine produktiven Daten, Zugangsdaten oder NAS-Verbindungen. Testbackend für 1.9.2 auf Port 4184. Native @Browser-Kontrolle und zuvor genehmigte lokale Playwright-Prüfung verwendet.

Belege in `docs/design-1.9.2/`: `comparison-desktop.png` zeigt 1.9.1 und 1.9.2 nebeneinander bei jeweils 1440 × 1024, DPR 1. `comparison-focus.png` vergleicht die Verbrauchskarten in Originalauflösung. Beide wurden visuell gemeinsam geprüft. Das ursprüngliche Variantenbild und die Prüfung von 1.9.1 bleiben unter `docs/design-1.9.1/` erhalten.

## Messbarer Platzgewinn

Messwerte aus `density-results.json`, gleiche Desktopgröße und Beispieldaten:

| Bereich | 1.9.1 | 1.9.2 |
| --- | ---: | ---: |
| Seitenleiste | 274 px | 240 px |
| Dashboard-Titel | 56 px | 36 px |
| Allgemeiner Inventartitel | 44,64 px | 31,68 px |
| Unterkante der Hauptkarten ab Bildschirmoberkante | 993 px | 761 px |
| Inventarzeile | 79 px | 55 px |
| Vollständig sichtbare Inventarzeilen bei Seitengröße 10 | 8 | 10 |

Die Einstellungsseite mit fünf aktivierten Beispielintegrationen benötigt ungefähr 20 % weniger Gesamthöhe. Ihre aktiven Werte wurden ausschließlich über schreibfreie Browser-Antwortfixtures dargestellt. Es wurde keine lokale oder produktive Integration aktiviert und keine Einstellung gespeichert. Die mobilen Modulzeilen ordnen ihre zwei Schalter nebeneinander unterhalb des Beschreibungstextes an. Die mobile Speicherleiste ist auf eine Zeile verkürzt; ihr gespeicherter/ungespeicherter Zustand bleibt über Statussymbol und zugänglichen Statustext erhalten.

## Fünf Gestaltungsebenen

| Ebene | Prüfung |
| --- | --- |
| Aufbau | Schmalere Navigation, kürzere Kopfzeile, unveränderte Inhaltsgruppen und Fachabläufe. Dashboard im 7:5-Raster, auf kleinen Geräten einspaltig. |
| Typografie | Gleiche lokalen Schriftdateien, kleinere Titel, weiterhin klare Titel-/Inhaltshierarchie. Zahlen, Fehlwerte und Einheiten lesbar. |
| Farben | Helles Salbei-Design und abgestimmter Dunkelmodus beibehalten; Kontrastfarben aus 1.9.1 unverändert. |
| Abstände | Kompakte Formulare, Tabellen, Registerkarten und Karten. Keine künstliche Dashboard-Mindesthöhe. Mobile Hauptaktionen behalten mindestens 44 Pixel Höhe. |
| Inhalte und Verhalten | Keine Angaben entfernt, keine simulierten Dashboardwerte, keine Änderung an Integrationswerten oder Speicherroutinen. Symbole weiter aus MDI. |

## Browser- und Funktionsprüfung

- 31 Kernprüfungen bestanden (`browser-results.json`): echte Dashboarddaten, Inventarsuche und Rücksprung, Ortsfilter und Zurücksetzen, vier Detailregister, Speichern/Wiederherstellen des Testgerätenamens, mobile Hauptaktionen und Suche, Dunkelmodus.
- Dashboard, Inventar und Gerätedetails ohne Seitenüberlauf bei 360, 390, 768, 960 und 1440 Pixeln. Bei 390 Pixeln zusätzlich Räume, Filament, LEGO, Netzwerk, Elektro, Verbrauch, Wartung, Wissen, Dokumente und Einstellungen geprüft.
- `density-results.json`: Einstellungsseite mit allen fünf aktiven Beispielintegrationen bei 360, 390 und 768 Pixeln ohne horizontalen Seitenüberlauf. Speicherleistenhöhe auf kleinen Displays zusätzlich geprüft.
- `mobile-followup.json`: Verbrauchswertspalten bei 360, 390, 599, 768, 960 und 1440 Pixeln auf Mindestbreite und Seitenüberlauf geprüft; mobile Werte bleiben lesbar.
- Keine JavaScript-Laufzeitfehler. Erwartete HTTP-409-Antworten auf nicht konfigurierte Home-Assistant-/Nextcloud-Integrationen in der isolierten Testdatenbank; keine externe Verbindungsprüfung.

Gefundene und behobene Designprobleme: übergroße Titel und Hauptaktionen, lange Tabellenzeilen, breite Navigation, unnötige Kartenabstände, hohe Modulzeilen und dreizeilige mobile Speicherleiste. Nachweise sind die Desktop-, Detail-, Inventar-, Einstellungs- und Mobilbilder im Belegordner. Keine offenen P0/P1/P2-Befunde im geänderten Umfang. P3: lange Einstellungsseiten bleiben bei vielen aktivierten Integrationen scrollbar; Beschreibungen werden nicht zur bloßen Höhenreduktion abgeschnitten.

## Technische Prüfung und Grenzen

Vue-Typprüfung, Produktionsbuild, 217 Frontendtests in 66 Dateien, 287 MDI-Symbole sowie Versions-, Release- und Brandingprüfung erfolgreich. Nach der Anpassung der Speicherleiste die drei Tests zur sicheren Einstellungsspeicherung zusätzlich erneut geprüft. Die bereits bestehende Warnung zum großen JavaScript-Bündel bleibt.

Backend-Anwendung, Migrationen, Backendtests, Anforderungen und Containerkonfiguration sind bytegleich mit 1.9.1; lediglich die Versionsangabe in `backend/pyproject.toml` ändert sich. Keine neue Migration, Head 0061. Integrations-, Formular- und Einstellungsspeicherroutinen bleiben unverändert. Paketvergleich in `source-integrity.json`.

Kein neuer Backend-Gesamtprüflauf oder Dockerbuild. Die dokumentierte Grenze aus 1.9.1 bleibt: ein in der unveränderten 1.9.0-Basis reproduzierter Fremdschlüssel-Testfehler; Testbackend unter Python 3.12 statt Docker-Python 3.13. Keine Prüfung realer Cloud-/NAS-/Drucker-Verbindungen. Deshalb weiterhin `full_quality_gate_passed: false`.

**Final result: passed** für die kompakte Darstellung und beschriebenen lokalen Kernabläufe. Die laufende NAS-/Docker-Installation wurde nicht verändert.
