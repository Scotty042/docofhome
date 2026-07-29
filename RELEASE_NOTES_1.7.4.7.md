# DocOfHome 1.7.4.7

Stand: 29.07.2026

Version 1.7.4.7 ergänzt die normale Schaltschrankübersicht um eine interaktive Verkabelungsanzeige. Die vollständige Leitungsansicht muss dadurch nicht dauerhaft geöffnet werden: Beim Überfahren eines elektrischen Elements werden nur dessen direkt angeschlossene Hauptleitungen sichtbar.

## Bedienung

- Mouse-over über Sicherung, FI/RCD, Zähler, DIN-Asset, Verteilerblock oder Schiene zeigt die direkt angeschlossenen Hauptverbindungen.
- Klick oder Antippen fixiert die Auswahl.
- Ein weiterer Klick auf dasselbe Element oder die Escape-Taste hebt die Fixierung auf.
- Das gewählte Element wird deutlich, seine direkten Nachbarn werden dezent hervorgehoben; nicht beteiligte Elemente treten optisch zurück.
- Im Modus **Verkabelung** wird weiterhin die vollständige Hauptverkabelung dargestellt.

## Darstellungsregeln

- Abgänge zu einzelnen Stromkreisen bleiben auch bei Mouse-over ausgeblendet.
- Manuelle Einspeisungen zu Sicherungen bleiben sichtbar.
- Beim Mouse-over einer konkreten Sicherung kann genau deren automatischer Kammschienenkontakt eingeblendet werden; beim Mouse-over der Kammschiene werden nicht sämtliche Einzelkontakte gezeichnet.
- FI/RCD behalten getrennte IN-/OUT-Anschlusspunkte.

## Technik

- reine Frontend-Erweiterung ohne Datenbankänderung;
- Alembic-Head bleibt `0049`.
