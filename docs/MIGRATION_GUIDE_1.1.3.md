# Migration auf DocOfHome 1.1.3

DocOfHome 1.1.3 korrigiert ausschließlich den Frontend-Build der Version 1.1.2.
Es gibt keine neue Datenbankmigration; Alembic bleibt auf Revision `0028`.

## Update

1. Ein Backup des persistenten `data`-Ordners erstellen.
2. Laufenden Container stoppen: `docker compose down`.
3. Den Quellstand durch DocOfHome 1.1.3 ersetzen.
4. Das Image ohne alten Build-Cache neu erstellen:

   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

5. Den Healthcheck und die Zählerschrankansicht prüfen.

Ein Datenbank-Downgrade ist für dieses reine Build-Fix nicht erforderlich.
