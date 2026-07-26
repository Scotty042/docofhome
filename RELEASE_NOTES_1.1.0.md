# DocOfHome 1.1.0 – Release Notes

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
