# Migration auf DocOfHome 1.3.2

## Vorbereitungen

1. In DocOfHome ein Backup erstellen.
2. Den vollständigen persistenten `data`-Ordner extern sichern.
3. Container stoppen.

## Update

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Beim Start wird Migration `0033` ausgeführt. Sie entfernt ausschließlich den
veralteten Unique-Index `uq_electrical_connections_active_target`. Bestandsdaten
werden nicht gelöscht oder umgeschrieben.

## Prüfung

Im Log darf kein Alembic-Fehler erscheinen. Anschließend zwei unterschiedliche
Quellen mit demselben Phasenverteilerblock verbinden. Beide Verbindungen müssen
in der Versorgungstopologie sichtbar sein.

Bei einer weiterhin erscheinenden Meldung zur alten Beschränkung den aktuellen
Alembic-Head im Container prüfen. Er muss `0033` sein.
