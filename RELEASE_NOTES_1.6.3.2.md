# DocOfHome 1.6.3.2 – Verbindliche Kammschienen-Autoverkabelung

Stand: 28. Juli 2026

## Anlass

Beim Speichern einer Phasen-/Kammschiene meldete die Anwendung weiterhin
„automatisch mit 0 Schutzgeräten verbunden“, obwohl in derselben sichtbaren
Reihe vollständig überdeckte Sicherungen vorhanden waren.

## Korrektur

Die Verteilerschrankansicht übermittelt beim Speichern die IDs der sichtbar und
vollständig überdeckten Schutzgeräte. Das Backend vertraut diesen IDs nicht
blind, sondern prüft jedes Gerät erneut auf aktive Existenz, Verteilung, Bereich,
Reihe, TE-Spanne und berechenbare Phase. Anschließend werden die abgeleiteten
Kontakte zwingend erzeugt.

Parallel bleibt eine unabhängige serverseitige Suche aktiv. Sie verbindet den
kanonischen Repositorypfad mit einem direkten, lebenszyklusgeprüften Tabellen-
Fallback für ältere aktualisierte SQLite-Datenbanken.

Für Bestände mit einer alten Eindeutigkeitsregel wird der neue Kontakt zunächst
inaktiv angelegt. Danach werden konkurrierende manuelle Einspeisungen und
Messbezüge umgehängt; erst anschließend wird der Kammschienenkontakt aktiviert.

## Ergebnis

- Quelle: Phasen-/Kammschiene;
- Ziel: jedes vollständig überdeckte aktive Schutzgerät;
- Phase: aus Startphase und TE-Position;
- allgemeine DIN-Assets bleiben unverbunden;
- ein erwarteter Kontakt darf nicht still fehlen.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0044`.
