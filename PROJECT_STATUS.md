# DocOfHome – Projektstatus

Stand: 27. Juli 2026

Release: 1.6.0

Alembic-Head: `0037`

DocOfHome 1.6.0 verbessert den Einrichtungsassistenten, die Backup-Benennung,
die Online-Bildsuche sowie die Sicherungs- und Zählerschrankansicht. Zusätzlich
können Sicherungsautomaten fachlich genauer und CT-/Stromwandlerklemmen eines
Smart Meters als Messpunkte an bestehenden Verkabelungen dokumentiert werden.

## Umgesetzter Funktionsstand

- Statusmeldungen im Einrichtungsassistenten werden beim Dienstwechsel
  zurückgesetzt;
- Abschlussnavigation mit Asset-Link und Fallback **Zur Übersicht**;
- neue Backup-Dateien heißen `DocOfHome-backup-*`, Legacy-Backups bleiben
  lesbar;
- DuckDuckGo Images mit Wikimedia-Fallback und Relevanzsortierung;
- Wasser-/Gaszähler aus der Elektro-Platzierung gefiltert;
- kompakte, farbcodierte Schrankansicht für Desktop und Tablet;
- Auslösecharakteristik und Nennstrom an Asset-Typ und Asset;
- empfohlener Asset-Typ **Stromstoßschalter** mit Spulen- und Kontaktdaten;
- Smart-Meter-Messkanäle mit Verbindung, Phase, Richtung, Wandlerdaten und
  Home-Assistant-Entitäten;
- Messpunkte in der elektrischen Topologie sichtbar;
- Handbuchtexte zu Sammelschiene, Kammschiene und CT-Klemmen erweitert.

## Daten- und Updatezustand

Migration `0037` ergänzt optionale Spalten und neue Messpunkt-Tabellen. Die
bestehenden Assets, Produkte, Verteilungen, Verkabelungen, Zählerstände,
Home-Assistant-Zuordnungen, Bilder und Dokumente werden nicht ersetzt.

Vor jedem Update ist ein vollständiges Backup des persistenten `data`-Ordners
erforderlich. Details stehen in `RELEASE_NOTES_1.6.0.md` und den Dokumenten unter
`docs/`.
