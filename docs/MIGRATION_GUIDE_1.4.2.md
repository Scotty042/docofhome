# Migration auf DocOfHome 1.4.2

1. In DocOfHome ein Backup erstellen.
2. Den persistenten `data`-Ordner zusätzlich extern sichern.
3. `docker compose down` ausführen.
4. Quellstand 1.4.2 einspielen.
5. `docker compose build --no-cache` ausführen.
6. `docker compose up -d` starten.
7. Logs und Healthcheck kontrollieren.

Beim Start führt Alembic Migration `0036` aus. Sie entfernt ausschließlich die
mit 1.4.1 eingeführten konfigurierbaren Projekt-, Impressums- und
Feedbackfelder. Fach- und Integrationsdaten bleiben unverändert.

Anschließend unter **Mehr → Über DocOfHome** prüfen:

- Version `1.4.2` wird angezeigt;
- kein Impressumsbereich ist vorhanden;
- Feedback ist ohne private Nextcloud-Konfiguration nutzbar;
- eine Testeinsendung erscheint als ZIP im fest hinterlegten File Drop.
