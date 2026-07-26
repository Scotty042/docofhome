# DocOfHome 1.2.1

DocOfHome 1.2.1 ist ein reines Dokumentations- und Statuspflege-Release auf
Basis von 1.2.0.

## Was wurde bereinigt?

- `PROJECT_STATUS.md` beschreibt jetzt eindeutig den aktuellen Release- und
  Freigabestatus.
- Der aktuelle Backlog besitzt eine eigene, datumsunabhängige Datei.
- Ein zentrales Sprintregister trennt historische Sprintverträge von aktiven
  oder geplanten Sprints.
- Der frühere Projektplan für `0.1.18-dev` bleibt vollständig im Archiv, wird
  aber nicht mehr als aktueller Plan angezeigt.
- Sprint 0039 für eine Info-, Changelog-, Impressums- und Feedbackseite ist als
  **Draft / Planning only** dokumentiert.
- Offene Zielsystem- und CI-Prüfungen von 1.2.x sind klar von Funktionssprints
  getrennt.

## Technische Auswirkungen

- keine Änderung an Anwendungscode oder API;
- keine neue Datenbankmigration;
- Alembic-Head bleibt `0029`;
- keine Änderung an bestehenden Daten oder Integrationskonfigurationen.

## Update

Ein Update von 1.2.0 auf 1.2.1 erfordert nur den üblichen Image-Neubau und
Containerneustart. Vor jedem Update bleibt ein vollständiges Backup empfohlen.
