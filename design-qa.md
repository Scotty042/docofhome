# Design- und Funktionsprüfung 1.9.3

30. Oktober 2026. Umfang: AMS-Lagerrollen und originale Bambu-Farbbilder. Grundlage ist die kompakte Oberfläche 1.9.2. Die laufende NAS-Sammlung wurde ausschließlich schreibfrei gelesen. Es wurden keine produktiven Einstellungen, Rollen oder Zuordnungen geändert und kein Cloud-/MQTT-Abruf ausgelöst.

## Befund und Änderung

Die bisherige AMS-Karte zeigte selbst bei eindeutiger Bindung lediglich `spool_label`. Die vorhandene Rollenliste enthält dagegen bereits Hersteller, Variante, Farbe, Bild und Restmenge. Die neue Anzeige verknüpft beide ausschließlich über die vorhandene `spool_id`. Sie zeigt Lagerangaben und AMS-Restmeldung mit getrennten Beschriftungen und öffnet die zugehörige Rolle. Ungebundene, leere, fehlende und archivierte Bindungen werden nicht durch eine Farbraterei ersetzt. Drucker werden getrennt gruppiert.

Die bisherige Store-Bildsuche konnte Cloud-Codes wie A00-P6 nicht zur Shop-Farbnummer auflösen. Der offizielle japanische Bambu-Shop stellt die ursprünglichen Hersteller-SKUs im öffentlichen Produktkatalog bereit. Daraus wird die exakte Farbnummer bestimmt und im offiziellen deutschen EU-Katalog auf ein eindeutiges Bild geprüft. Vorhandene Shop-Farbnummern werden direkt verwendet. Keine Bildsuche anhand ähnlicher Farben. Die gemeinsame Aktion ergänzt ausschließlich aktive Bambu-Rollen ohne Bild, behält manuelle Bilder bei und meldet einzelne ungelöste Fälle.

## Visuelle Prüfung

Belege unter `docs/design-1.9.3/`: `ams-desktop.png`, `ams-mobile.png` und `collection-store-images.png`. Desktop 1440 × 1024 und mobile Ansicht 390 Pixel breit visuell geprüft. Die Bildreferenz ist das vom Nutzer gezeigte Bambu-Modellbild; `bambu-hellgrau.png` ist das tatsächlich aus dem offiziellen Katalog heruntergeladene Originalbild nach lokaler Größenbegrenzung. Kein KI-Ersatz und keine nachgezeichnete Produktgrafik.

| Gestaltungsebene | Ergebnis |
| --- | --- |
| Aufbau | Kompakte Karten pro AMS-Platz, gruppiert je Drucker, mit Direktzugriff auf die Lagerrolle. |
| Typografie | Rollennamen und Farbe vor technischen IDs, gut umbrechende Bezeichnungen und Seriennummern. |
| Farben | Gespeicherte Farbwerte plus Text; leere Plätze neutral, kein verbliebener Filamentfarbton als scheinbare Belegung. |
| Abstände | Gemeinsames kompaktes Design aus 1.9.2; einspaltige mobile Karten und ausreichend große Schaltflächen. |
| Bilder und Inhalte | Originalbilder aus dem Store; vorhandene Lagerbilder werden wiederverwendet. Fehlender Farbname zeigt Farbcode statt erfundener Bezeichnung. |

Gefundene und behobene Probleme: Darstellung der Rollen-ID statt der Lagerbezeichnung; keine direkte Detailöffnung; schwer durchsuchbare ID-Auswahl; unaufgelöste Cloud-Produktcodes bei der Bildsuche; farbiger Platzhalter für leer gemeldeten Slot. Der erste automatisierte Überlauftest prüfte während der Navigationsanimation; nach abgeschlossenem Layoutwechsel bei allen Breiten ohne Überlauf bestätigt. Dialogschließung und Datenaktualisierung werden vor Screenshots bzw. Prüfungen abgewartet.

Keine offenen P0/P1/P2-Befunde im geänderten Umfang. Grenze: unbekannte oder nicht mehr im offiziellen Katalog vorhandene Varianten/Codes benötigen eine Shopnummer oder manuelle Bildzuordnung. Das ist sichtbar ausgewiesen. Es wird keine vollständige Abdeckung aller historischen Bambu-Filamente behauptet.

## Verifikation

- `browser-results.json`: AMS mit gebundener Lagerrolle, echten Originalbildern in lokalen Testantworten, Restmenge null/0, ungebundenen und leeren Slots, Detailöffnung, Suche und Speicherung der exakten Rollen-ID sowie gemeinsame Bildübernahme geprüft. Antworten auf Zuordnungs-/Bildänderungen wurden ausschließlich lokal simuliert. Kein produktiver Schreibzugriff. Keine JavaScript-Laufzeitfehler.
- AMS bei 360, 390, 768, 960 und 1440 Pixeln ohne horizontalen Seitenüberlauf. Screenshot bei 390 Pixeln als Ganzseitenbeleg.
- `official-store-live-check.json`: öffentlicher Live-Abruf in einer isolierten lokalen Testdatenbank erfolgreich: A00-P6 → 10202 / Magenta; 10104 → Hellgrau und genau der vom Nutzer genannten Bildquelle. Fehlende Farbnamen/Shopnummern werden ergänzt, bestehende Texte nicht überschrieben.
- 223 Frontendtests in 67 Dateien bestanden, einschließlich neuer Fälle für exakte Bindung, gleiche Farben, leere/archivierte Rollen, Nullwerte und gemeinsame Bildübernahme.
- 16 gezielte Filament-Backendtests bestanden, einschließlich eindeutiger SKU-Auflösung, Ablehnung mehrdeutiger/prefixähnlicher Codes und Erhalt eigener Farbnamen.
- Vue-Typprüfung und Produktionsbuild bestanden. 289 MDI-Symbole gültig; Versions- und Releaseprüfung bestanden.
- Keine neue Migration. Containerkonfiguration, Einstellungen, Cloud-Anmeldung, Synchronisierung und AMS-Identitätslogik unverändert. Änderungen am Backend beschränken sich auf die Store-Bildsuche und deren Tests; siehe `source-integrity.json`.

Die bekannten Backend-Gesamtprüfgrenzen aus 1.9.1 gelten weiter. Keine Docker-/Python-3.13-Gesamtprüfung und kein Test echter Drucker-/Bambu-Konten. Öffentliche Store-Formate und Katalogbestände können sich ändern. Daher bleibt `full_quality_gate_passed: false`.

**Final result: passed** für die geänderte Anzeige, die lokal geprüften Abläufe und die ausdrücklich genannten zwei Live-Bildbeispiele. Die produktive Installation blieb unverändert.
