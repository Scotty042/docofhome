# DocOfHome

DocOfHome 1.6.1 ist ein lokaler digitaler Zwilling für die technische
Hausdokumentation. Die Anwendung verwaltet Assets, Orte, Elektroinstallation,
Netzwerk, Verbrauch, Wartungen, Wiki, Bilder, Dokumente und optionale
Integrationen wie Home Assistant, Immich und Nextcloud.

## Neu in 1.6.1

- separater, atomarer Zählerwechsel mit Schluss- und Startstand sowie sichtbarem
  letztem Zählerstand und OBIS-Hinweisen;
- mehrere PV-Zähler können gemeinsam für das Dashboard ausgewertet werden;
- konfigurierbare Online-Produktbildquellen mit kombinierter,
  deduplizierter Relevanzsortierung;
- direkte elektrische Vor- und Nachfolger am Asset sowie gruppierte
  Phasenabgänge in der Topologie;
- einheitliche Erkennung und Zählung aktiver Sicherungs-/Schutzgeräte;
- primäre Netzwerkschnittstelle und erweiterte Home-Assistant-Rollen für
  smarte Relais/DIN-Schaltaktoren;
- Standard-Stammdaten für **Smartes Relais / DIN-Schaltaktor** und
  **Shelly Pro 1**.

## Neu in 1.6.0

- stabilerer Einrichtungsassistent mit schrittspezifischen Statusmeldungen,
  zuverlässiger Abschlussnavigation und manuellem Fallback;
- neue Backup-Namen mit `DocOfHome-backup-`; ältere
  `tectoryn-backup-`-Archive bleiben kompatibel;
- DuckDuckGo Images als primäre Online-Produktbildsuche mit Relevanzbewertung
  und Wikimedia Commons als Fallback;
- PC- und Tablet-orientierte Sicherungs-/Zählerschrankansicht mit kompakten
  Namen, optionalem Livewert beziehungsweise B16-Kurzangabe, Typfarben und
  Legende;
- Wasser- und Gaszähler werden nicht mehr als unplatzierte Elektrogeräte
  angeboten;
- Auslösecharakteristik und Nennstrom als Stammdaten und Asset-Override;
- empfohlener Standard-Asset-Typ **Stromstoßschalter** mit Spulenspannung,
  Spannungsart, Kontaktanzahl und Kontaktart;
- Smart-Meter-Messpunkte für CT-/Stromwandlerklemmen an vorhandenen
  Verkabelungen einschließlich eigener Home-Assistant-Entitäten;
- ausführlichere Handbucherklärung für Sammelschiene und Kammschiene.

## Betrieb und Sicherheitsmodell

DocOfHome ist für ein vertrauenswürdiges privates Netzwerk vorgesehen und darf
nicht ungeschützt aus dem Internet erreichbar sein. Änderungen und Arbeiten an
elektrischen Anlagen gehören in die Hände einer Elektrofachkraft. DocOfHome
dokumentiert den Bestand und ersetzt keine Planung, Prüfung oder
Sicherheitsberatung.

## Installation mit Docker Compose

```bash
cp .env.example .env
docker compose build
docker compose up -d
docker compose ps
```

DocOfHome ist standardmäßig unter `http://localhost:8088` erreichbar. Beim
Start werden die Alembic-Migrationen bis Head `0038` ausgeführt. Der persistente
Ordner `./data` enthält Datenbank, Uploads, Backups und Laufzeitdaten und gehört
nicht in ein Quellcode-Release.

## Update von 1.6.0 auf 1.6.1

1. In DocOfHome ein Backup erstellen und den persistenten `data`-Ordner extern
   sichern.
2. Container stoppen: `docker compose down`.
3. 1.6.1 in einen neuen, sauberen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. `docker compose build --no-cache` und `docker compose up -d` ausführen.
6. Migration `0038`, Healthcheck, Logs, Backups, Zählerwechsel, PV-Auswertung,
   Produktbildquellen und Elektro-/Netzwerkansichten prüfen.

Migration `0038` ergänzt die neuen Einstellungen und Stammdaten, erlaubt mehrere
PV-Dashboardzähler und erweitert Netzwerk- sowie Home-Assistant-Zuordnungen.
Bestehende Daten bleiben erhalten.

## Entwicklung und Qualitätsprüfung

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/python -m pytest

cd ../frontend
npm ci
npm test
npm run build

cd ..
docker compose build --no-cache
```

## Weitere Informationen

- [Projektstatus](PROJECT_STATUS.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Release Notes 1.6.1](RELEASE_NOTES_1.6.1.md)
- [Migrationsanleitung](docs/MIGRATION_GUIDE_1.6.0.md)
- [Validierungsbericht](docs/VALIDATION_REPORT_1.6.0.md)
- [Bekannte Grenzen](docs/KNOWN_LIMITATIONS_1.6.0.md)

Lizenz: siehe [LICENSE](LICENSE).
