# DocOfHome 1.7.4.5

Stand: 29.07.2026

Version 1.7.4.5 korrigiert die räumliche und elektrische Aussagekraft der Schaltschrank-Verkabelung sowie die Kandidatenlisten in Unterverteilungen.

## Änderungen

- Der Hausanschluss wird am unteren Rand der Verkabelungsansicht dargestellt.
- Ein platzierter Zähler wird über sein verknüpftes Asset direkt am tatsächlichen Zählerfeld verankert.
- FI/RCD besitzen getrennte Anschlusszonen **IN** und **OUT**. Dadurch bleibt sichtbar, dass L und N das Gerät durchlaufen und eine nachgelagerte N-Schiene nicht direkt am Hausanschluss hängt.
- Die Listen „Noch nicht platzierte DIN-Assets“ und „Noch nicht platzierte Zähler“ berücksichtigen aktive Platzierungen in allen Verteilungen.
- Kandidaten werden auf den Ort der aktuellen Verteilung sowie Assets/Zähler ohne Ortszuordnung begrenzt.
- Die Topologie lädt aktive Schrankkomponenten aller Haupt- und Unterverteilungen zusätzlich nach. Dadurch stehen auch Kammschienen der aktuellen Unterverteilung als Quelle oder Ziel bereit.

## Technik

- Neue globale Leseendpunkte für aktive Asset- und Zählerplatzierungen.
- Keine Datenbankmigration; Alembic-Head bleibt `0049`.
