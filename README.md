# DocOfHome

DocOfHome 1.5.0 ist ein lokaler digitaler Zwilling für die technische
Hausdokumentation. Die Anwendung verwaltet Assets, Orte, Elektroinstallation,
Netzwerk, Verbrauch, Wartungen, Wiki, Bilder, Dokumente, logische Dienste und
eine nachvollziehbare Änderungshistorie.

## Neu in 1.5.0

Unter **Wiki → Handbuch & Glossar** steht eine vollständig offline nutzbare
Einstiegshilfe bereit. Sie enthält 109 zentrale Begriffe aus den Bereichen
Assets, Elektro, Netzwerk, Verbrauch, Home Assistant, Bilder/Dokumente und
Betrieb. Suche, Kategorienfilter, A–Z-Glossar, interne Anker und eine responsive
Mobilansicht sind direkt im Frontend enthalten.

Die bestehende editierbare Wiki-Funktion bleibt unter **Wiki → Wiki-Seiten**
unverändert erhalten. In der Detailansicht eines assetgebundenen DIN-Geräts kann
nun zusätzlich die normale Asset-Bearbeitung geöffnet werden. Passive
Schrankkomponenten bleiben ohne Asset-Button.

## Betrieb und Sicherheitsmodell

DocOfHome ist für eine Installation in einem vertrauenswürdigen privaten
Netzwerk vorgesehen und besitzt derzeit keine Benutzeranmeldung. Die Anwendung
darf nicht direkt aus dem Internet erreichbar sein. Home Assistant, Immich,
Nextcloud und FRITZ!Box sind optional; ohne Integrationen bleiben alle lokalen
Kernmodule einschließlich Handbuch nutzbar.

Änderungen an elektrischen Anlagen gehören in die Hände einer
Elektrofachkraft. DocOfHome dokumentiert den Bestand und ersetzt keine Planung,
Prüfung oder Sicherheitsberatung.

## Installation mit Docker Compose

Voraussetzungen sind Docker Engine mit Compose v2, Git und ein freier
TCP-Port. Das offizielle Image wird auf Docker Hub als
`scotty042/docofhome:1.5.0` veröffentlicht.

```bash
git clone https://github.com/Scotty042/docofhome.git
cd docofhome
cp .env.example .env
docker compose pull
docker compose up -d --no-build
docker compose ps
```

Danach ist DocOfHome standardmäßig unter `http://localhost:8088` erreichbar.
Beim ersten Start werden die vorhandenen Alembic-Migrationen automatisch bis
Head `0036` ausgeführt.

Alternativ kann der exakt versionierte Container direkt geladen werden:

```bash
docker pull scotty042/docofhome:1.5.0
```

Für einen lokalen Build aus dem Quellcode bleibt
`docker compose build --no-cache` verfügbar.

Der persistente Ordner `./data` enthält Datenbank, lokale Backups, Cache,
Protokolle und gegebenenfalls eine vorbereitete Wiederherstellung. Er gehört
nicht in die Versionsverwaltung oder in ein Quellcode-Release.

## Update von 1.4.2-r3 auf 1.5.0

1. In der laufenden Oberfläche ein lokales ZIP-Backup erzeugen und den
   persistenten `data`-Ordner zusätzlich extern sichern.
2. Container stoppen: `docker compose down`.
3. Den bisherigen Quellstand getrennt aufbewahren und 1.5.0 in einen sauberen
   Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. Offizielles Image laden und starten: `docker compose pull` und
   `docker compose up -d --no-build`.
6. Healthcheck, Logs, vorhandene Wiki-Seiten, Handbuchsuche und eine
   DIN-Asset-Bearbeitung praktisch prüfen.

Für 1.5.0 gibt es keine neue Datenbankmigration. Bestehende Gebäude-, Asset-,
Elektro-, Verbrauchs-, Netzwerk-, Wiki- und Integrationsdaten bleiben
unverändert.

## Funktionsschwerpunkte

- Gebäudestruktur, Standorte, Assets, Produkte und Dokumentverknüpfungen;
- Haupt- und Unterverteilungen mit TE-Raster, Schutzgeräten, DIN-Assets und
  passiven Schrankkomponenten;
- Sammelschienen, FI-Gruppen, N-Schienen, automatische Phasenzuordnung und
  mehrere Einspeisungen;
- Netzwerkgeräte, Schnittstellen, Ports, VLANs, IP-Netze und Verkabelung;
- Verbrauchszähler, mobile Zählerstandserfassung und Zeitraumauswertungen;
- Home-Assistant-, Immich-, Nextcloud- und FRITZ!Box-Integration;
- statisches Handbuch & Glossar sowie weiterhin editierbare Wiki-Seiten;
- lokale Backups, Wiederherstellung, Releasehistorie und Feedbackfunktion.

Technische Kompatibilitätskennungen wie `jarvis_code`, das Präfix `JARVIS_` und
der bestehende SQLite-Dateiname bleiben bewusst unverändert.

## Backup und Wiederherstellung

Lokale Backups sind immer verfügbar. Optional kann ein Backup nach einer
expliziten Benutzeraktion nach Nextcloud kopiert werden. Vor einem Restore
validiert DocOfHome Manifest und Prüfsumme und legt eine Sicherheitskopie der
aktuellen Datenbank an.

Empfohlen sind ein lokales und externes Backup vor jedem Update, eine regelmäßige
Kopie des gesamten persistenten `data`-Ordners und gelegentliche
Wiederherstellungsproben auf einem getrennten System.

## Entwicklung und Qualitätsprüfung

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
.venv/Scripts/python -m ruff check app tests
.venv/Scripts/python -m mypy app
.venv/Scripts/python -m pytest
```

Frontend:

```bash
cd frontend
npm ci
npm test
npm run build
```

Docker und Laufzeit:

```bash
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

## Weitere Informationen

- [Projektstatus](PROJECT_STATUS.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Release Notes](RELEASE_NOTES_1.5.0.md)
- [Migrationsanleitung](docs/MIGRATION_GUIDE_1.5.0.md)
- [Validierungsbericht](docs/VALIDATION_REPORT_1.5.0.md)
- [Bekannte Grenzen](docs/KNOWN_LIMITATIONS_1.5.0.md)

Lizenz: siehe [LICENSE](LICENSE).
