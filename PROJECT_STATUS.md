# DocOfHome – Projektstatus

Stand: 27. Juli 2026

Release: 1.6.1

Alembic-Head: `0038`

DocOfHome 1.6.1 bündelt Korrekturen für Zählerwechsel, PV-Dashboard,
Produktbildquellen, elektrische Topologie, Schutzgeräte, Netzwerkschnittstellen
und smarte DIN-Schaltaktoren.

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

Migration `0038` ergänzt optionale Einstellungen, Rollen, Indizes und
Standard-Stammdaten. Die
bestehenden Assets, Produkte, Verteilungen, Verkabelungen, Zählerstände,
Home-Assistant-Zuordnungen, Bilder und Dokumente werden nicht ersetzt.

Vor jedem Update ist ein vollständiges Backup des persistenten `data`-Ordners
erforderlich. Details stehen in `RELEASE_NOTES_1.6.1.md` und den Dokumenten unter
`docs/`.
