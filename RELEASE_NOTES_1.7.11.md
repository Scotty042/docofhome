# DocOfHome 1.7.11

Diese Korrektur stabilisiert die MCP-Rezeptsuche bei einem leeren Kochbuch. Optionale
Suchfilter dürfen fehlen oder als `null` übertragen werden. Die Antwort besitzt stets die
Form `{"items": [...], "count": n}`. Bei leerem Bestand wird damit zuverlässig
`{"items": [], "count": 0}` geliefert und die anschließende Rezepterstellung kann fortfahren.

Keine Datenbankmigration; Alembic-Head bleibt `0052`.
