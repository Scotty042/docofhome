# Implementierungszusammenfassung 1.7.3

## Backend

`ElectricalTopologyService` erkennt explizite Verbindungen, die ausschließlich
N und/oder PE führen. Für diese Verbindungen werden keine Außenleiteranforderungen
aus parallelen physischen Einspeisungen übernommen. Effektive Leiter,
Phasenherkunft, Sperrstatus und Warnungen bleiben verbindungsspezifisch.

Die aggregierte Versorgung eines Endpunkts wird unverändert aus allen
Eingangsverbindungen gebildet. Dadurch zeigt ein FI/RCD weiterhin insgesamt
L1/L2/L3/N, während die einzelne Neutralleiterverbindung ausschließlich N zeigt.

## Frontend

Die Außenleiterbindung wird nur aktiviert, wenn die aktuell bearbeitete
Verbindung tatsächlich L1, L2 oder L3 enthält oder eine automatisch verwaltete
Phasenschienenverbindung ist. Eine reine N-/PE-Auswahl kann daher angelegt und
bearbeitet werden, ohne automatisch um L1/L2/L3 erweitert zu werden.

## Migration

Keine neue Migration. Alembic-Head bleibt `0049`.
