# DocOfHome

DocOfHome 1.6.2 ist ein lokaler digitaler Zwilling für die technische
Hausdokumentation. Die Anwendung verwaltet Assets, Orte, Elektroinstallation,
Netzwerk, Verbrauch, Wartungen, Wiki, Bilder, Dokumente und optionale
Integrationen wie Home Assistant, Immich und Nextcloud.

## Neu in 1.6.2

- automatisch erzeugte, idempotente Monatsableseaufgaben;
- getrennte Dashboardkacheln für PV-Erzeugung und Netzeinspeisung;
- wirksame Phasen mit Warnung bei abweichenden Bestandsverbindungen;
- Haupt-/Unterverteilungen als strukturelle Behälter;
- Verteilerdosen ohne sichtbares TE-Raster;
- Kamm-/Phasenschienen als Overlay oberhalb oder unterhalb der Schutzgeräte;
- feste Repository- und Releaseinformationen in Anwendung und ZIP.

## Neu in 1.6.1

- separater, atomarer Zählerwechsel mit Schluss- und Startstand sowie sichtbarem
  letztem Zählerstand und OBIS-Hinweisen;
- mehrere PV-Zähler können gemeinsam für das Dashboard ausgewertet werden;
- konfigurierbare Online-Produktbildquellen;
- direkte elektrische Vor- und Nachfolger sowie gruppierte Phasenabgänge;
- einheitliche Erkennung aktiver Sicherungs-/Schutzgeräte;
- smarte Relais/DIN-Schaltaktoren und primäre Netzwerkschnittstellen.

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
Start werden die Alembic-Migrationen bis Head `0039` ausgeführt. Der persistente
Ordner `./data` enthält Datenbank, Uploads, Backups und Laufzeitdaten und gehört
nicht in ein Quellcode-Release.

## Update von 1.6.1 auf 1.6.2

1. Backup erstellen und den persistenten `data`-Ordner extern sichern.
2. Container stoppen: `docker compose down`.
3. 1.6.2 in einen neuen, sauberen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. `docker compose build --no-cache` und `docker compose up -d` ausführen.
6. Migration `0039`, Healthcheck, Aufgaben, Dashboard und Topologie prüfen.

Bestehende Daten bleiben erhalten; widersprüchliche alte Phasen werden sichtbar
gekennzeichnet und nicht automatisch verändert.

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
- [Release Notes 1.6.2](RELEASE_NOTES_1.6.2.md)
- [Migrationsanleitung](docs/MIGRATION_GUIDE_1.6.0.md)
- [Validierungsbericht](docs/VALIDATION_REPORT_1.6.0.md)
- [Bekannte Grenzen](docs/KNOWN_LIMITATIONS_1.6.0.md)

Lizenz: siehe [LICENSE](LICENSE).
