# Migration auf DocOfHome 1.2.1

DocOfHome 1.2.1 enthält keine Schemaänderung. Alembic-Head bleibt `0029`.

## Von 1.2.0 auf 1.2.1

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Es wird keine neue Migration ausgeführt. Bestehende Daten und Einstellungen
bleiben unverändert.

## Von 1.1.3 oder älter

Bei einem direkten Update gelten zusätzlich die Migrationsschritte aus
`MIGRATION_GUIDE_1.2.0.md`. Vor dem Update:

1. lokales DocOfHome-Backup erstellen;
2. gesamten persistenten `data`-Ordner extern sichern;
3. bisherigen Quellstand separat aufbewahren;
4. Update zunächst mit einer Datenbankkopie testen.

## Nachkontrolle

- Startseite und Navigation öffnen;
- Projektstatus und Roadmap im Quellpaket prüfen;
- Alembic-Head `0029` bestätigen;
- bei direktem Update von älteren Versionen zusätzlich HA-Seite,
  Asset-Zuordnungen, Produktbilder und Zählerschrank prüfen.
