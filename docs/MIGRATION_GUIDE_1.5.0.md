# Migrationsanleitung DocOfHome 1.5.0

Stand: 26. Juli 2026  
Ausgangsbasis: DocOfHome 1.4.2-r3  
Alembic-Head vor und nach dem Update: `0036`

## Vor dem Update

1. In DocOfHome ein lokales Backup erzeugen.
2. Den vollständigen persistenten `data`-Ordner zusätzlich extern sichern.
3. Die bisherige Compose-Datei und lokale `.env` getrennt aufbewahren.
4. Container stoppen: `docker compose down`.

## Update

1. Das Release in einen neuen, leeren Quellordner entpacken.
2. Die eigene `.env` und notwendige lokale Compose-Anpassungen übernehmen.
3. Keine Datenbank oder Uploadordner aus dem Release in das Datenverzeichnis
   kopieren.
4. Image neu bauen: `docker compose build --no-cache`.
5. Starten: `docker compose up -d`.

## Besonderheit von 1.5.0

Es gibt keine neue Datenbankmigration. Handbuch und Glossar sind statische
Frontend-Inhalte. Bestehende Wiki-Seiten, Assets, Elektro- und Netzwerkdaten,
Zählerstände, Bilder und Integrationszuordnungen werden nicht verändert.

## Prüfung nach dem Start

- Healthcheck und Containerstatus kontrollieren;
- **Wiki → Wiki-Seiten** öffnen und vorhandene Inhalte prüfen;
- **Wiki → Handbuch & Glossar** öffnen;
- nach `Sammelschiene`, `FI`, `N-Schiene`, `VLAN`, `DHCP`, `Asset` und
  `Zählerstand` suchen;
- Kategorienfilter und Glossar A–Z testen;
- eine Verteilung öffnen und bei einem DIN-Asset **Asset bearbeiten** testen;
- prüfen, dass eine passive Schrankkomponente keinen Asset-Button zeigt;
- Containerlogs auf Exceptions prüfen.
