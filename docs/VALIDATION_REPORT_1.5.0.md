# Validierungsbericht DocOfHome 1.5.0

Stand: 26. Juli 2026  
Ausgangsbasis: `DocOfHome-1.4.2-r3.zip`  
Zielversion: DocOfHome 1.5.0  
Alembic-Head: `0036`

## 1. Umgesetzter Umfang

- statische Route `/wiki/handbuch` unter der Navigation **Wiki**;
- bestehende editierbare Wiki-Seiten unverändert unter `/wiki`;
- zentrale Frontend-Datenstruktur mit 109 Begriffen in acht Kategorien;
- lokale Suche über Begriff, Alias, Beschreibung, Beispiel, Kategorie und
  verwandte Begriffe;
- Kategorienfilter, einklappbare Handbuchabschnitte, Inhaltsverzeichnis,
  interne Ankerlinks und Glossar A–Z;
- responsive Desktop- und Mobilstruktur ohne Backend- oder Internetabhängigkeit;
- Elektro-Sicherheitshinweis;
- Button **Asset bearbeiten** bei Schutzgeräten und normalen DIN-Assets;
- kein Asset-Button bei passiven Schrankkomponenten;
- keine Datenbankmigration; Alembic-Head bleibt `0036`.

## 2. Tatsächlich erfolgreich ausgeführte Prüfungen

- `python scripts/check-version.py`;
- `python scripts/check-branding.py`;
- `python scripts/check-collected-fixes.py`;
- `python scripts/check-reading-reminders.py`;
- alle statischen Releaseverträge von 1.2.4 bis 1.5.0;
- `python -m compileall -q backend/app backend/migrations backend/tests scripts`;
- TypeScript-Compile-Prüfung der zentralen Handbuch-Datenstruktur mit globalem
  TypeScript 5.8.3;
- ausgeführte JavaScript-Laufzeitprüfung der kompilierten Handbuchlogik:
  109 Begriffe, Suche nach DHCP und Kammschiene sowie A–Z-Sprungmarken;
- Prüfung, dass `frontend/package-lock.json` gegenüber 1.4.2-r3 ausschließlich
  die beiden eigenen Versionsfelder von 1.4.2 auf 1.5.0 ändert;
- Prüfung, dass die transitive Abhängigkeit `rfdc` unverändert auf 1.4.1 bleibt;
- statische Prüfung der Route, Navigation, zentralen Begriffe, mobilen Struktur
  und beiden Asset-Bearbeitungswege;
- statische Prüfung, dass der Detailblock passiver Schrankkomponenten keinen
  Button **Asset bearbeiten** enthält.

## 3. Blockierte oder nicht ausführbare Prüfungen

### Frontend: npm, Vitest, vue-tsc und Vite

`npm ci` wurde zweimal tatsächlich gestartet. Beide Versuche scheiterten beim
Download von `why-is-node-running-2.3.0.tgz` mit HTTP 503 vom internen
Paket-Proxy. Da `npm ci` nicht erfolgreich abgeschlossen wurde, konnten
`npm test`, der vollständige `vue-tsc --noEmit`-Lauf und `vite build` in dieser
Arbeitsumgebung nicht seriös ausgeführt werden.

Diese Prüfungen werden ausdrücklich **nicht als bestanden** gewertet.

### Backend: Ruff, mypy und Pytest

Die Befehle wurden aufgerufen. `ruff` und `mypy` sind in der Arbeitsumgebung
nicht installiert. Pytest konnte wegen der fehlenden Abhängigkeit `sqlmodel`
nicht bis zur Testsammlung gelangen.

Der anschließende tatsächliche Installationsversuch mit
`python -m pip install -r requirements-dev.txt` scheiterte am internen
Paketindex, der keine passende FastAPI-Version für `fastapi>=0.116,<0.117`
bereitstellte.

Die vollständigen Backendtests werden daher ausdrücklich **nicht als bestanden**
gewertet.

### Docker

`docker compose build --no-cache` wurde aufgerufen und scheiterte unmittelbar,
weil Docker in der Arbeitsumgebung nicht installiert ist. Image-Build,
Containerstart, Healthcheck, Logprüfung und praktische Browserprüfung konnten
hier nicht erfolgen und werden **nicht als bestanden** gewertet.

## 4. Verbindliche Zielsystemprüfung

In einer Umgebung mit erreichbaren npm-/Python-Paketquellen und Docker:

```bash
cd frontend
npm ci
npm test
npm run build

cd ../backend
python -m pip install -r requirements-dev.txt
ruff check app tests
mypy app
python -m pytest -q

cd ..
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Danach praktisch prüfen:

1. vorhandene Wiki-Seiten öffnen und bearbeiten;
2. **Wiki → Handbuch & Glossar** öffnen;
3. nach `Sammelschiene`, `Phasenschiene`, `FI`, `N-Schiene`, `VLAN`, `DHCP`,
   `Asset` und `Zählerstand` suchen;
4. Kategorienfilter, A–Z-Sprungmarken und interne Anker testen;
5. Desktop- und Smartphone-Darstellung prüfen;
6. bei Schutzgerät und normalem DIN-Asset **Asset bearbeiten** öffnen,
   speichern und die aktualisierten Daten in der Verteilung kontrollieren;
7. bei einer passiven Schrankkomponente kontrollieren, dass kein Asset-Button
   angezeigt wird;
8. Healthcheck und Logs auf Exceptions prüfen.

## 5. Bewertung

Der Quellstand, die statischen Inhalte, Versionsquellen und Releaseverträge sind
lokal geprüft. Das Release ist für die Zielsystemprüfung vorbereitet. Wegen der
beschriebenen Infrastrukturblockaden ist es kein vollständig durch npm, Pytest
und Docker verifiziertes Release; dieser Reststatus wird bewusst nicht
verschleiert.
