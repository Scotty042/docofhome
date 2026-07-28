# DocOfHome 1.6.3.7 – Validierung

## Ziel

Prüfung, dass neue Sicherungen und sonstige Hutschienengeräte einheitlich über
DIN-Assets und `electrical_asset_placements` geführt werden, während bestehende
Legacy-Schutzgeräte weiterhin lesbar und verwaltbar bleiben.

## Geprüfte Verträge

- regulärer Neuanlagebutton: `DIN-Gerät platzieren`
- kein sichtbarer Neuanlagebutton für neue `protective_devices`
- Kammschienenservice unterstützt `asset`-Ziele aus DIN-Platzierungen
- Legacy-Ziele vom Typ `protective_device` bleiben rückwärtskompatibel
- Versionskonsistenz 1.6.3.7
