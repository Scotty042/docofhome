# Migration auf DocOfHome 1.2.3

DocOfHome 1.2.3 enthält keine Schemaänderung. Alembic-Head bleibt `0029`.

## Von 1.2.2 auf 1.2.3

1. lokales Anwendungsbackup und Sicherung des persistenten `data`-Ordners
   erstellen;
2. Container mit `docker compose down` stoppen;
3. Quellstand 1.2.3 einspielen;
4. Image mit `docker compose build --no-cache` neu bauen;
5. mit `docker compose up -d` starten;
6. Containerstatus und Frontend prüfen.

Es wird keine neue Migration ausgeführt. Bei einem direkten Update von 1.1.3
oder älter gelten zusätzlich die Migrationshinweise aus 1.2.0.
