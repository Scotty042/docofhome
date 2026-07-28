# DocOfHome 1.7.1 – Umsetzungsübersicht

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
