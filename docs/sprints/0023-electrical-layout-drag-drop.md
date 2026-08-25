# Sprint 0023 – Drag-and-drop im Verteilungseditor

## Status

Lokal implementiert und geprüft.

## Ziel

Schutzgeräte lassen sich auf einem Desktop mit Maus direkt auf die gewünschte Reihe und
Modulposition ziehen. Die bestehende Formularbedienung bleibt für Touchgeräte, kleine Bildschirme
und die präzise Korrektur technischer Werte vollständig erhalten.

## Umfang

- Ziehen bereits platzierter Schutzgeräte auf eine andere Modulposition
- Ziehen noch nicht positionierter Schutzgeräte aus der Sammelliste
- sichtbare Drop-Ziele für jedes Modul während eines Ziehvorgangs
- unmittelbare Warnung bei Überlappung oder Überschreitung der Reihenkapazität
- Übernahme von Reihe und Startmodul in den Dialog, wenn die Gerätebreite noch fehlt
- Speichern über denselben bestehenden und serverseitig validierten Positionsendpunkt
- verständliche Stromkreis-Erklärungen in Liste, Editor und Detailansicht
- unveränderte dialogbasierte Bedienung auf Mobil- und Touchgeräten

## Abnahme

- ein Gerät mit bekannter Breite kann per Maus auf eine freie Position verschoben werden
- belegte oder zu kleine Zielbereiche werden nicht gespeichert
- ein Gerät ohne Breitenangabe öffnet nach dem Ablegen den Positionsdialog
- alle Icon-, Typ-, Frontend- und Produktions-Build-Prüfungen sind erfolgreich
