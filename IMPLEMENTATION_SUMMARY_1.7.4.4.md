# Implementation Summary 1.7.4.4

Die Verkabelungslogik des Overlays wurde so angepasst, dass Anschlusspunkte an internen Geräten nicht mehr allein aus der Rolle als Quelle oder Ziel abgeleitet werden. Stattdessen entscheidet die relative Lage des Gegenpunkts, ob die Leitung an der Ober- oder Unterkante des Bauteils ansetzt.

## Umgesetzt

- `representedAnchor()` liefert jetzt die vollständige Geometrie eines sichtbaren Endpunkts.
- `choosePort()` wählt den Anschlusspunkt abhängig von der vertikalen Lage des Gegenpunkts.
- `orthogonalPath()` führt auf- und absteigende Leitungen direkt in die benötigte Richtung und hält dabei den vorhandenen Aderabstand bei.
- Bestehende Regeln zum Ausblenden einzelner Stromkreise und LS-/RCBO-Abgänge bleiben unverändert bestehen.
