# DocOfHome 1.1.1 – Release Notes

Veröffentlicht am 23. Juli 2026.

## Behobener Fehler

Im Release 1.1.0 wurden unter **Wartung & Aufgaben** nur Zähler mit einem
expliziten monatlichen Ableseplan berücksichtigt. Bestehende Zähler, die über
die bereits vorhandene globale Regel **„Ablesung nach Tagen als fällig
markieren“** verwaltet werden, erschienen dort nicht.

DocOfHome 1.1.1 korrigiert dieses Verhalten:

- monatliche Ablesepläne funktionieren unverändert;
- Zähler ohne Monatsplan verwenden die globale X-Tage-Fälligkeit;
- Zähler ohne bisherige Ablesung sind sofort fällig;
- der Abschnitt **Ableseerinnerungen** ist auf der Wartungsseite immer sichtbar;
- bei keiner aktuellen Fälligkeit erscheint ein verständlicher Leerstatus;
- „Jetzt ablesen“ öffnet weiterhin direkt den betroffenen Zähler.

## Kompatibilität

Das Release enthält den vollständigen Stand von DocOfHome 1.1.0 einschließlich
Sprint 0038 **Photovoltaik und Energiebilanz**. Es gibt keine neue
Datenbankmigration. Der Alembic-Head bleibt `0027_energy_balance`.
