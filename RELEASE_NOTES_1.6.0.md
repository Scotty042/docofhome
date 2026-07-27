# DocOfHome 1.6.0 – Elektroansicht und Smart-Meter-Messpunkte

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
