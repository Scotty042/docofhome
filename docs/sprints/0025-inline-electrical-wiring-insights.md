# Sprint 0025 – Versorgungsinformationen direkt am Schutzgerät

## Status

Lokal implementiert und geprüft.

## Ziel

Phase, Einspeisung und nachgelagerte Verbraucher sind bereits beim Blick auf die Verteilung oder
eine Sicherung sichtbar. Die zentrale Topologie bleibt die einzige Datenquelle; ein manueller
Umweg über die allgemeine Verkabelungsseite ist für die Übersicht nicht mehr nötig.

## Umfang

- Phasenchips L1, L2, L3, N und PE auf Schutzgerätekarten
- Anzeige der ursprünglichen Einspeisung
- Summen aller nachgelagerten Schutzgeräte, Stromkreise und Assets
- Kennzeichnung noch nicht verkabelter Elemente
- direkter, fokussierter Sprung zur betroffenen Zeile im Versorgungsbaum
- bei fehlender Verbindung ein bereits auf das Schutzgerät vorbelegter Verkabelungsdialog
- Versorgungszusammenfassung auf der Verteilungsdetailseite
- dieselbe Übersicht im Schutzgeräteeditor
- verständliche Mouse-over-Hinweise für Phasen, Kennzahlen und Aktionen
- kompakte, in normalen Verteilerfeldern vollständig sichtbare 12er-Hutschienen ohne wiederholten
  Drag-and-drop-Hinweis innerhalb jedes Schutzgeräts
- ausfallsichere Darstellung: Die Verteilung bleibt nutzbar, falls die Topologie nicht geladen
  werden kann

## Abgrenzung

- keine zweite, abweichende Verkabelungsdatenhaltung in den Verteilerkarten
- keine automatische Annahme einer Phase aus der Modulposition
- keine automatische Erzeugung elektrischer Verbindungen
- keine Berechnung von Last, Selektivität oder normgerechter Absicherung

## Abnahme

- eine Sicherung zeigt ihre dokumentierten Phasen direkt im Sicherungskasten
- Einspeisung und alle nachgelagerten Elemente sind ohne Seitenwechsel erkennbar
- der Versorgungsweg wird mit der gewählten Sicherung im sichtbaren Bereich geöffnet
- eine unverkabelte Sicherung wird beim Anlegen als Ziel vorausgewählt
- Frontend-Tests, Typprüfung, Icon-Prüfung und Produktions-Build sind erfolgreich
