# Validierungsbericht DocOfHome 1.4.2

Stand: 25. Juli 2026  
Ausgangsbasis: DocOfHome 1.4.1  
Zielversion: DocOfHome 1.4.2  
Alembic-Head: `0036`

## 1. Umgesetzter Umfang

- Impressum aus Info-Seite, Settings-Oberfläche, Settings-API und Datenmodell entfernt;
- Projekt- und spätere GitHub-Verweise in eine zentrale Quellcodedatei verschoben;
- Feedback ohne private Nextcloud-Integration direkt aktiviert;
- festes öffentliches Nextcloud-File-Drop-Ziel ausschließlich im Backend;
- Feedbackpaket als ZIP mit `feedback.md`, `metadata.json` und `README.txt`;
- Größenlimit, serverseitiger Zufallsname und bestehendes Rate-Limit;
- technische Angaben weiterhin nur nach ausdrücklicher Zustimmung;
- Migration `0036_remove_configurable_about_fields`.

## 2. Tatsächlich erfolgreich ausgeführte Prüfungen

- Versionsabgleich von `VERSION`, Backend, Frontend und Lockdatei;
- Python-Compile-Prüfung für Backend, Migrationen, Tests und Scripts;
- statische Releaseverträge bis 1.4.2;
- isolierter Upgrade-/Downgrade-/Upgrade-Test der Migration `0036`;
- Quellprüfung, dass Info- und Einstellungsseite kein Impressum und keine
  pflegbaren About-Felder mehr enthalten;
- Unit-Testvertrag für Ableitung des öffentlichen WebDAV-Endpunkts und die
  erforderlichen Upload-Header;
- Unit-Testvertrag für ZIP-Inhalt, Größenbegrenzung und Zustimmung zu
  technischen Angaben;
- Release-ZIP entpackt und alle Manifestdateien anhand von Pfad, Größe und
  SHA-256 gegengeprüft.

## 3. Nicht vollständig ausführbare Prüfungen

### Frontend

Ein vollständiger `npm ci`, Vitest-, `vue-tsc`- und Vite-Lauf kann nur als
bestanden dokumentiert werden, wenn die Paketquellen in der Arbeitsumgebung
erreichbar sind. Andernfalls bleibt der Docker-Build auf dem Zielsystem das
verbindliche Qualitätsgate.

### Backend

Der vollständige Pytest-, Ruff- und mypy-Lauf hängt von den installierten
Entwicklungsabhängigkeiten ab. Ausgeführte Teilprüfungen werden nicht als Ersatz
für den vollständigen Lauf dargestellt.

### Öffentlicher File Drop

Die Arbeitsumgebung konnte `hal.scott91.de` nicht per DNS erreichen. Ein realer
Testupload in den bereitgestellten Ordner war daher nicht möglich. Die
Implementierung folgt dem öffentlichen Nextcloud-WebDAV-Endpunkt und setzt den
für schreibende Anfragen vorgesehenen Header `X-Requested-With`.

### Docker

Steht Docker in der Arbeitsumgebung nicht zur Verfügung, müssen Image-Build,
Containerstart, Migration, Healthcheck und praktischer Upload auf dem NAS
geprüft werden.

## 4. Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach eine Feedback-Testnachricht senden und prüfen, ob ein ZIP im öffentlichen
File Drop erscheint. Zusätzlich sicherstellen, dass die Info-Seite kein
Impressum und die Einstellungen keine Projekt-/Feedbackfelder mehr anzeigen.
## 5. Buildkorrektur r2

Beim ersten 1.4.2-Paket wurde die Projektversion versehentlich auch auf den
transitiven npm-Eintrag `rfdc` angewendet. Dadurch verwies die Lockdatei auf die
nicht veröffentlichte Version `rfdc@1.4.2`. Das korrigierte r2-Paket stellt die
ursprüngliche Abhängigkeit `rfdc@1.4.1` inklusive Download-URL wieder her.

Zusätzlich prüft `scripts/check-release-1.4.2.py` diesen Lockdatei-Eintrag, damit
dieser Fehler bei einer erneuten Paketierung erkannt wird. Der vollständige
`npm ci`-Lauf konnte in der Arbeitsumgebung wegen HTTP-503-Antworten des internen
Paket-Gateways nicht abgeschlossen werden.

## 6. Buildkorrektur r3

Der NAS-Build des r2-Pakets erreichte `vue-tsc`, meldete in
`SettingsPage.vue` jedoch fehlende Eigenschaften `requiredRule` und
`integrationMeta`. Beim Entfernen der konfigurierbaren About-, Impressums- und
Feedbackabschnitte waren diese weiterhin von den unveränderten
Integrationskarten verwendeten Hilfen versehentlich ebenfalls gelöscht worden.

Für r3 wurden die Definitionen aus dem zuvor vorhandenen, funktionalen
Einstellungsstand unverändert wiederhergestellt. Zusätzlich prüfen nun sowohl
`frontend/src/pages/aboutPage.test.ts` als auch
`scripts/check-release-1.4.2.py`, dass beide Definitionen vorhanden bleiben.

Tatsächlich ausgeführt wurden für r3:

- `python scripts/check-version.py`;
- `python scripts/check-release-1.4.2.py`;
- `python -m compileall -q backend/app backend/migrations scripts`;
- Vergleich der Einstellungsseite mit 1.4.1, wobei nur die bewusst entfernten
  About-/Impressums-/Feedbackbereiche und deren nun unbenutzte Hilfen fehlen;
- erneute Manifestprüfung des entpackten Releasepakets.

Ein vollständiger lokaler `npm ci`-/`vue-tsc`-/Vite-Lauf konnte in dieser
Arbeitsumgebung nicht abgeschlossen werden, weil die Paketinstallation nicht
vollständig durchlief. Der Docker-Build auf dem Zielsystem bleibt deshalb das
abschließende Qualitätsgate. Der konkret gemeldete TS2339-Ursprung ist im
r3-Quellstand beseitigt.

