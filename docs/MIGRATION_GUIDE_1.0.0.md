# Migration auf DocOfHome 1.0.0

## Unterstützter Ausgangsstand

Der geprüfte direkte Upgradepfad beginnt bei `0.1.18-dev` mit Alembic-Revision
0023. Ältere Installationen müssen zunächst ihre bisherige Migrationskette bis
0023 ausführen.

## Vorgehen

1. In DocOfHome ein lokales ZIP-Backup erstellen.
2. Backup und persistenten Datenordner zusätzlich außerhalb des Hosts sichern.
3. Container mit `docker compose down` stoppen.
4. Release-Dateien einspielen, `.env` und `data` unverändert lassen.
5. `docker compose build --no-cache` ausführen.
6. Mit `docker compose up -d` starten.
7. `docker compose ps` und `/api/v1/health/ready` prüfen.
8. Stichproben für Assets, Archiv, Dokumentlinks, Verbrauch und Integrationen
   durchführen.

Beim Start führt der Container `alembic upgrade head` aus. Die Migration 0024
prüft vorhandene Inventarnummern vor dem Unique-Index. Bei einem Konflikt wird
das Upgrade verständlich abgebrochen, ohne Werte umzuschreiben; die Dublette
muss anschließend fachlich bereinigt werden.

## Wiederanlauf nach abgebrochener Migration 0024

Die finale Releasefassung erkennt verwaiste SQLite-Arbeitstabellen mit dem
Präfix `_alembic_tmp_`, die bei einem zuvor abgebrochenen Alembic-Batchlauf
zurückbleiben können. Existieren Original und Arbeitstabelle, wird nur die
unvollständige Arbeitstabelle verworfen. Existiert nur die Arbeitstabelle, wird
der bereits ausgeführte Batchschritt fertiggestellt. Die Migration prüft
anschließend Spalten, Indizes und Seed-Daten und läuft idempotent bis Revision
0026 weiter.

Auch für diesen automatischen Wiederanlauf muss vor dem Austausch des Images
eine Kopie des persistenten `data`-Ordners angelegt werden. Manuelle
SQL-Löschbefehle an der produktiven Datenbank sind nicht erforderlich.

## Rückkehr

Vor einer Rückkehr immer das vor dem Update erstellte vollständige Backup
verwenden. Technische Downgrades der Migrationen 0026 bis 0024 sind geprüft,
entfernen jedoch die in diesen Tabellen/Feldern seit dem Update erfassten
1.0-Daten. Für produktive Installationen ist daher die Wiederherstellung des
Backups die sichere Methode.
