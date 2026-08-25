# DocOfHome 1.7.4.8

Stand: 24.08.2026

Version 1.7.4.8 korrigiert die automatische Zählerablesungslogik unter
**Wartung & Aufgaben**.

## Korrekturen

- **Monatsende:** Die Fälligkeit liegt immer auf dem tatsächlichen letzten
  Kalendertag (28/29/30/31).
- **Gültiges Ablesefenster:** Standardmäßig beginnt es drei Tage vor der
  Fälligkeit. Eine frühere Ablesung im selben Monat erledigt die Aufgabe nicht.
- **Verspätete Ablesung:** Das Fenster bleibt bis zum Beginn des nächsten
  Monatsfensters offen. So kann eine Ablesung nach dem Monatswechsel noch die
  Vormonatsaufgabe schließen, ohne die neue Aufgabe vorzeitig zu erledigen.
- **Überfälligkeit:** Offene Monatsaufgaben bleiben nach Monatsende sichtbar.
- **Weitere Erinnerungstage:** Werte wie `28` bedeuten den 28. Kalendertag des
  Monats und niemals „28 Tage vorher“.
- **Einheitlichkeit:** Reminder-API und automatischer Aufgabengenerator verwenden
  dieselben Datumshelfer und Ablesefenster.

## Update und Datenbank

- Vor dem Update wird weiterhin ein vollständiges Backup empfohlen.
- Es gibt keine Schemaänderung und keine neue Migration.
- Alembic-Head bleibt `0049`.
