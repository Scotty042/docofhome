# DocOfHome 1.6.3.7

Diese Korrektur vereinheitlicht das Daten- und Bedienmodell für Geräte auf der
DIN-Hutschiene.

## Einheitliches Modell

Neue Sicherungen, FI/RCD, FI/LS, Relais, Stromstoßschalter und andere
Hutschienengeräte werden als normale Assets angelegt und anschließend über eine
DIN-Platzierung (`electrical_asset_placements`) in den Verteiler gesetzt. Sie werden nicht mehr über den
separaten Schutzgeräte-Neuanlageweg erzeugt.

Der bisherige `protective_devices`-Pfad bleibt ausschließlich zur
Rückwärtskompatibilität mit bereits vorhandenen Datensätzen bestehen.

## Bedienung

- Die Schrankansicht zeigt nur noch **DIN-Gerät platzieren** als regulären
  Neuanlageweg.
- Der Dialog verwendet weiterhin die am Asset, Produkt oder Asset-Typ
  hinterlegte DIN-Breite.
- Phasen-/Kammschienen verbinden alle vollständig überdeckten DIN-Platzierungen
  automatisch.
- Bestehende Legacy-Schutzgeräte werden weiterhin angezeigt, verschoben,
  archiviert und in der Topologie berücksichtigt.
