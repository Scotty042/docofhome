# Migration auf DocOfHome 1.2.2

DocOfHome 1.2.2 enthält keine Schemaänderung. Alembic-Head bleibt `0029`.

## Von 1.2.1 auf 1.2.2

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Es wird keine neue Migration ausgeführt. Das Patch-Release korrigiert nur ein
nicht verfügbares Frontend-Icon. Bestehende Daten und Einstellungen bleiben
unverändert.

## Von 1.1.3 oder älter

Bei einem direkten Update gelten zusätzlich die Migrationsschritte aus
`MIGRATION_GUIDE_1.2.0.md`. Vor dem Update ein vollständiges Backup des
persistenten `data`-Ordners erstellen und den Start zuerst mit einer
Datenbankkopie prüfen.

## Nachkontrolle

- Docker-Image ohne MDI-Fehler bauen;
- Asset anlegen oder bearbeiten;
- Dialog **Neues Label** öffnen;
- Label anlegen und direkte Zuordnung prüfen;
- Alembic-Head `0029` bestätigen.
