# Implementation Summary 1.7.4.8

Die Monatsablesungsregeln wurden in
`backend/app/services/consumption_reminders.py` zusammengeführt.

## Umsetzung

- kalenderkorrekte Fälligkeit für feste Ablesetage und den letzten Monatstag;
- gemeinsames, nicht überlappendes Ablesefenster je Monatsfälligkeit;
- Standardvorlauf von drei Tagen sowie zusätzliche konkrete Erinnerungstage;
- eindeutige Zuordnung verspäteter Ablesungen zur offenen Vormonatsfälligkeit;
- API-Rückblick auf eine offene Vormonatsfälligkeit;
- Aufgaben-Synchronisierung für aktuellen Monat, Vormonat und bereits offene
  ältere automatisch erzeugte Aufgaben;
- automatische Erledigung nur bei einer Ablesung innerhalb des gültigen Fensters;
- keine Frontend-Änderung erforderlich, da API- und Work-Item-Verträge stabil bleiben;
- keine Datenbankänderung; Alembic-Head `0049`.
