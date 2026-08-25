# ADR-0019: Drag-and-drop verwendet den validierten Positionsendpunkt

## Status

Akzeptiert

## Entscheidung

Drag-and-drop ist ausschließlich eine zusätzliche Desktop-Bedienung für die bereits vorhandene
Schutzgerätepositionierung. Das Ablegen erzeugt keinen separaten Speicherweg, sondern sendet
Bereich, Reihe, Startposition und Gerätebreite an denselben API-Endpunkt wie der Positionsdialog.
Damit bleiben Kapazitäts-, Vollständigkeits- und Überlappungsregeln serverseitig verbindlich.

Die Oberfläche prüft offensichtliche Überschneidungen und einen Überstand am Reihenende vorab, um
schnelles und verständliches Feedback zu geben. Diese Prüfung ersetzt nicht die abschließende
Validierung im Backend. Fehlt die bekannte Gerätebreite, wird nicht automatisch eine Breite
angenommen; stattdessen öffnet sich der Dialog mit übernommener Zielposition.

## Folgen

- Mausbedienung wird schneller, ohne einen zweiten fachlichen Schreibpfad einzuführen
- Touchgeräte und kleinere Bildschirme behalten die explizite Dialogbedienung
- konkurrierende oder veraltete Browserstände werden weiterhin vom Backend sicher abgewiesen
- technische Werte werden nicht aus der Darstellung geraten oder automatisch erfunden
