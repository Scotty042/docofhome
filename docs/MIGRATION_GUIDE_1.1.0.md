# Migration auf DocOfHome 1.1.0

## Unterstützter Ausgangsstand

Der direkte Upgradepfad ist für DocOfHome `1.0.0`, einschließlich Fixstand 1
und Fixstand 2, mit Alembic-Revision `0026` vorgesehen. Die vollständige
Migrationskette ab einer leeren Datenbank bleibt erhalten.

## Vorbereitung

1. In der laufenden Installation ein lokales ZIP-Backup erstellen.
2. Backup und den gesamten persistenten `data`-Ordner außerhalb des Hosts
   sichern.
3. Den vorhandenen 1.0-Quellstand separat aufbewahren.
4. Container mit `docker compose down` stoppen.

## Update

1. Release-Dateien einspielen; `.env` und `data` unverändert lassen.
2. Image neu bauen: `docker compose build --no-cache`.
3. Starten: `docker compose up -d`.
4. Status prüfen: `docker compose ps`.
5. Bereitschaft prüfen: `/api/v1/health/ready`.
6. Unter **Verbrauch → PV & Energiebilanz** die drei Bilanzzähler zuordnen.
7. Strom- und Gasvergleich auf dem Dashboard sowie Ableseerinnerungen unter
   **Wartung & Aufgaben** kontrollieren.

Beim Start führt DocOfHome `alembic upgrade head` aus.

## Migration 0027

`0027_energy_balance`:

- erweitert den erlaubten Zählertyp um `electricity_feed_in`;
- entfernt nur den Unique-Index, der bisher mehrere Einspeisungen auf dasselbe
  Elektro-Topologie-Ziel verhinderte;
- erzeugt `energy_configurations` und `energy_components`;
- legt eine leere Energiekonfiguration an.

Bestehende Zähler, Ablesungen, Assets, Topologieverbindungen und Einstellungen
werden nicht geändert. Ein lokaler Test mit Nutzdaten bestätigte den Pfad
`0026 -> 0027` sowie den Erhalt vorhandener Datensätze.

## Rückkehr

Die sichere Rückkehr ist die Wiederherstellung des vor dem Update erstellten
Backups. Der technische Downgrade `0027 -> 0026` entfernt Energiekomponenten
und Energiekonfiguration. Weil Revision 0026 nur eine eingehende Versorgung pro
Topologie-Ziel erlaubt, muss vor einem Downgrade außerdem jedes Ziel auf
höchstens eine aktive Versorgung reduziert werden; andernfalls kann der alte
Unique-Index nicht wiederhergestellt werden.
