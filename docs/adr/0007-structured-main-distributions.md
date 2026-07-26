# ADR 0007 – Strukturierte Hauptverteilungen

## Status

Akzeptiert

## Kontext

Normale Unterverteilungen lassen sich sinnvoll als Folge von Reihen und Modulen darstellen. Haupt- und Zählerverteiler können dagegen aus mehreren vertikalen Feldern bestehen, die unterschiedliche Funktionen enthalten. Ein rein globales Reihenmodell vermischt Geräte aus räumlich getrennten Feldern und bildet Zähler-, Anschluss-, Technik- oder Reservebereiche nicht ab.

## Entscheidung

`ElectricalDistribution` erhält den Layoutmodus `rows` oder `sections`.

- `rows` bleibt der Standard und einzige Modus für Unterverteilungen.
- `sections` ist ausschließlich für Hauptverteilungen zulässig.
- Ein Feld wird durch `ElectricalDistributionSection` beschrieben.
- Ein Bereich innerhalb eines Feldes wird durch `ElectricalDistributionArea` beschrieben.
- Nur Bereiche vom Typ `device_rows` tragen Reihen- und Modulkapazität.
- Schutzgeräte werden über die optionale `area_id` einem Bereich zugeordnet.
- Die Position eines Schutzgeräts wird innerhalb des Bereichs validiert.
- Technische Gerätedaten und physische Platzierung werden über getrennte Operationen geändert.

## Folgen

- Bestehende Verteilungen bleiben ohne Datenänderung im Reihenmodus.
- Mehrspaltige Hauptverteiler können realitätsnah dargestellt werden.
- Positionsüberlappungen zwischen unterschiedlichen Feldern sind ausgeschlossen, weil die Prüfung bereichsbezogen erfolgt.
- Nicht modulare Bereiche können dokumentiert werden, ohne künstliche Reihen oder Geräte anzulegen.
- Die Benutzeroberfläche benötigt eine eigene Schrankaufteilung für strukturierte Hauptverteilungen.
