# Migration auf DocOfHome 1.4.1

1. In DocOfHome ein Backup erstellen.
2. Den persistenten `data`-Ordner zusätzlich extern sichern.
3. `docker compose down` ausführen.
4. Quellstand 1.4.1 einspielen.
5. `docker compose build --no-cache` ausführen.
6. `docker compose up -d` starten.
7. Logs und Healthcheck kontrollieren.

Beim Start führt Alembic Migration `0035` aus. Sie ergänzt nur optionale
Projekt-, Impressums- und Feedbackfelder. Feedback bleibt deaktiviert, bis es in
den Einstellungen ausdrücklich eingeschaltet und Nextcloud vollständig
konfiguriert wurde.
