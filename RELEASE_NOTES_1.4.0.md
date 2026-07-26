# DocOfHome 1.4.0

DocOfHome 1.4.0 macht die Schrankaufteilung für eine private Hausdokumentation
übersichtlicher und ergänzt eine einfache, nachvollziehbare Logik für
Sammelschienen, FI/RCD-Gruppen und Neutralleiterschienen.

## Sammelschienen

Eine Sammelschiene wird als passive Schrankkomponente angelegt. Zusätzlich zu
Reihe und Startposition werden die überspannten TE, die vorhandenen Phasen, eine
Startphase und optional der speisende FI/RCD hinterlegt.

Beispiel mit Startphase L1:

```text
TE 1  L1
TE 2  L2
TE 3  L3
TE 4  L1
TE 5  L2
TE 6  L3
```

Sammelschienen liegen als Überlagerung unter den Schutzgeräten und blockieren
deren TE-Platz nicht. Andere Bauteile kollidieren weiterhin wie bisher.

## FI- und Neutralleiter-Zuordnung

- Eine Sammelschiene kann einem FI/RCD zugeordnet werden.
- Eine N-Schiene kann demselben FI/RCD zugeordnet werden.
- Schutzgeräte unter der Sammelschiene erhalten daraus automatisch die wirksame
  FI-Gruppe, die passende N-Schiene und ihre Phase.
- Manuelle Zuordnungen bleiben möglich.
- Abweichungen werden als verständliche Warnung angezeigt, nicht als unnötige
  harte Sperre.

Die automatisch ermittelten Werte werden nicht ungefragt als manuelle Werte in
das Schutzgerät geschrieben. Verschieben per Drag-and-drop kann die wirksame
Gruppe daher korrekt neu berechnen.

## Optimierte Schrankansicht

- Belegte und freie TE, nicht platzierte Geräte und Hinweise auf einen Blick;
- kompakte und erweiterte Darstellung;
- Phasen-, FI- und N-Schienen-Anzeige direkt am Schutzgerät;
- Sammelschiene als eigene Leiste mit Phasenfolge;
- Detailpanel für Schutzgerät, Schrankkomponente und DIN-Asset;
- separate Ablage für noch nicht platzierte Schutzgeräte und DIN-Assets;
- Drag-and-drop auf dem Desktop und weiterhin dialogbasierte Positionierung auf
  kleinen Bildschirmen.

## Migration

Alembic `0034_home_electrical_groups` ergänzt optionale Felder. Bestehende
Verbindungen, Geräte, Platzierungen und Schrankkomponenten werden nicht gelöscht
oder automatisch umgedeutet.
