# DocOfHome 1.2.2

DocOfHome 1.2.2 behebt einen Frontend-Buildfehler aus 1.2.1.

## Korrektur

Die verpflichtende MDI-Prüfung meldete:

```text
Nicht verfügbare MDI-Icons: mdi-label-plus-outline
```

Das Icon wurde im Button und im Dialog zur Inline-Anlage von Asset-Labels durch
`mdi-tag-plus-outline` ersetzt. Dieses Icon ist in der festgeschriebenen
Abhängigkeit `@mdi/font` 7.4.47 vorhanden und beschreibt die Aktion fachlich
passend.

## Technische Auswirkungen

- keine Änderung an Backend, API oder Datenmodell;
- keine neue Datenbankmigration;
- Alembic-Head bleibt `0029`;
- bestehende Daten und Einstellungen bleiben unverändert.

## Update

Ein Update von 1.2.1 auf 1.2.2 erfordert den üblichen Image-Neubau und
Containerneustart. Vor dem Update bleibt ein vollständiges Backup empfohlen.
