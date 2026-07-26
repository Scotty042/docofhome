# Migration auf DocOfHome 1.1.1

DocOfHome 1.1.1 ist ein reines Korrekturrelease zu 1.1.0. Die Datenbankstruktur
ändert sich nicht; Alembic bleibt auf `0027_energy_balance`.

## Vorgehen

1. In DocOfHome ein Backup erzeugen und den persistenten `data`-Ordner sichern.
2. Container mit `docker compose down` stoppen.
3. Die 1.1.1-Quelldateien einspielen.
4. Image mit `docker compose build --no-cache` neu bauen.
5. Anwendung mit `docker compose up -d` starten.
6. Unter **Wartung & Aufgaben** den sichtbaren Abschnitt
   **Ableseerinnerungen** prüfen.

Bestehende Zähler benötigen keinen monatlichen Ableseplan. Ohne Monatsplan wird
die globale Einstellung **„Ablesung nach Tagen als fällig markieren“**
verwendet. Ein vorhandener Monatsplan hat weiterhin Vorrang.
