# Sprint definitions

Dieses Verzeichnis enthält historische und zukünftige Sprintverträge von
DocOfHome.

## Aktueller Planungseinstieg

Vor jeder Entwicklung sind in dieser Reihenfolge zu lesen:

1. [`PROJECT_STATUS.md`](../../PROJECT_STATUS.md)
2. [`docs/CURRENT_STATUS_AND_BACKLOG.md`](../CURRENT_STATUS_AND_BACKLOG.md)
3. [`docs/SPRINT_REGISTER.md`](../SPRINT_REGISTER.md)
4. [`ROADMAP.md`](../../ROADMAP.md)

Derzeit gibt es **keinen aktiven freigegebenen Sprint**. Sprint 0039 wurde mit
Release 1.4.1 abgeschlossen.

## Bedeutung historischer Statuszeilen

Sprintdateien bleiben nach Abschluss als vollständige historische Verträge im
Repository. Sie werden nicht rückwirkend umgeschrieben, um frühere Abweichungen
oder Zwischenstände zu verbergen. Deshalb können einzelne Dateien alte Angaben
wie „Approved“, „Live-Abnahme ausstehend“ oder „Docker validation pending“
enthalten.

Diese Angaben sind nicht die aktuelle Releasefreigabe. Die heutige Einordnung
steht im zentralen [`Sprintregister`](../SPRINT_REGISTER.md).

## Verbindlicher Ablauf für neue Sprints

1. Sprintdatei aus `TEMPLATE.md` erstellen.
2. Status `Draft / Planning only` setzen.
3. Fachlichkeit, Datenmodell, Migration, Sicherheit, Tests und Abnahme klären.
4. Erst nach ausdrücklicher Freigabe auf `Approved` setzen.
5. Nur den ausgewählten Sprint implementieren.
6. Alle Qualitätsgates aus Sprint und Entwicklungsrichtlinien ausführen.
7. Erst nach erfüllter Definition of Done auf `Completed` setzen.

Ein Roadmap-Eintrag, eine Chatnotiz oder ein möglicher Versionsname ersetzt keine
Sprintfreigabe.

## Dateikonvention

```text
0039-about-changelog-imprint-feedback.md
0040-next-topic.md
```

Die Nummern 0034 bis 0037 sind historisch nicht als Sprintdateien vorhanden und
werden nicht nachträglich wiederverwendet.

## Aktuell relevante Dateien

- [0038 – Photovoltaik und Energiebilanz](0038-photovoltaic-energy-balance.md)
- [0039 – Über DocOfHome, Changelog, Impressum und Feedback](0039-about-changelog-imprint-feedback.md) – abgeschlossen mit 1.4.1
- [Sprintvorlage](TEMPLATE.md)
