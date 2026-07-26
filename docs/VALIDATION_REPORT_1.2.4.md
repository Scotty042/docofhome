# Validierungsbericht DocOfHome 1.2.4

Stand: 24.07.2026

- Ausgangsbasis: `DocOfHome-1.2.3.zip`
- Zielversion: `1.2.4`
- Datenbankbasis: Alembic `0029`
- neuer Alembic-Head: `0030`
- Prüfplattform: Python 3.13.5, Node.js 22.16.0, npm 10.9.2,
  TypeScript 5.8.3

Dieser Bericht trennt bestandene Prüfungen von Prüfungen, die in der
bereitgestellten Ausführungsumgebung nicht möglich waren. Nicht ausgeführte
Tests werden nicht als bestanden gewertet.

## Umgesetzte Regressionen

### Online-Produktbildsuche

- Backend-Suche bleibt der erste Suchweg.
- Bei Netzwerkfehlern, HTTP 502 oder HTTP 5xx wird auf die Wikimedia-Suche im
  Browser mit `origin=*` gewechselt.
- Bild- und Quell-URLs werden ausschließlich für freigegebene Wikimedia-Hosts
  akzeptiert.
- Vorherige Such- und Importvorgänge werden bei einem neuen Vorgang abgebrochen.
- Suche, Bilddownload und lokaler Upload besitzen Zeitlimits.
- Der ausgewählte Treffer wird über den vorhandenen Upload-Endpunkt lokal in
  DocOfHome gespeichert, wenn der Container das Bild nicht selbst laden kann.
- Fehlerzustände für Backend-Ausfall, externen Ausfall, leere Trefferlisten und
  fehlgeschlagenen Download beziehungsweise Upload sind sichtbar.

### Schrankaufteilung

- Die Schrankaufteilung ist aus jeder aktiven Haupt- und Unterverteilung
  erreichbar.
- Einfache Reihenaufteilungen werden auf der Schrankseite angezeigt.
- Noch nicht konfigurierte Verteilungen zeigen einen leeren Zustand mit Aktion
  zum Anlegen.
- Unterverteilungen dürfen den Feld-/Bereichsmodus verwenden.
- Migration `0030` entfernt ausschließlich die frühere Einschränkung für den
  Aufbau einer Unterverteilung.

### Netzwerkseite

- Die fehlende Einbindung von `NetworkInterfaceType`, die beim Erzeugen der
  Netzwerkübersicht einen `NameError` verursachen konnte, wurde ergänzt.
- Ältere oder unbekannte Enum-Werte werden beim Lesen auf neutrale Werte
  abgebildet.
- Die sieben Seitenanfragen werden fehlertolerant geladen; erfolgreich geladene
  Teilbereiche bleiben bei einem Einzelfehler sichtbar.
- Die bestehende Regel bleibt unverändert: freie Switch-Ports sind neutral und
  die Verkabelungsprüfung erfolgt auf Geräteebene.

### Globale Benachrichtigungen

- Globale FIFO-Warteschlange für Erfolg, Fehler, Warnung und Information.
- Darstellung oben mittig mit `z-index: 10000`, oberhalb von Dialogen und
  Vollbilddialogen.
- Fehler bleiben länger sichtbar als Erfolgsmeldungen und können manuell
  geschlossen werden.
- Bei der mobilen Zählerstandserfassung bleibt der Dialog bei einem Fehler mit
  den Eingaben geöffnet. Während des Requests sind Ladezustand und Sperre der
  Speichern-Schaltfläche aktiv. Nach Erfolg schließt der Dialog und die
  Bestätigung wird global angezeigt.

## Tatsächlich bestandene Prüfungen

| Prüfung | Ergebnis |
|---|---|
| `python3 scripts/check-version.py` | Bestanden; Versionsquellen sind `1.2.4` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden; 10 bestehende Fix-Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| `python3 scripts/check-release-1.2.4.py` | Bestanden; statische Verträge der vier Fehlerkorrekturen vorhanden |
| `python3 scripts/check-migration-0030.py` | Bestanden; Upgrade, Downgrade und erneutes Upgrade gegen eine repräsentative SQLite-0029-Tabelle |
| `python3 -m compileall -q backend/app backend/tests backend/migrations scripts` | Bestanden |
| TypeScript-Transpilierung aller `.ts`-Dateien und aller Vue-`script setup`-Blöcke | Bestanden; keine Syntaxdiagnosen |
| `tsc --noEmit ... productImageSearch.ts frontend/src/types/assets.ts` | Bestanden; strikte semantische Prüfung des neuen Browser-Fallback-Dienstes |
| `git diff --check` | Bestanden; keine Whitespacefehler |
| lokale Markdown-Linkprüfung | Bestanden |
| grundlegende Prüfung auf private Schlüssel und produktive `.env`-Dateien | Bestanden; bekannte Testwerte sind keine produktiven Zugangsdaten |

Die eigenständige Migrationsprüfung verwendet die echte Upgrade- und
Downgrade-Funktion aus
`0030_enable_subdistribution_sections.py`. Dabei wurde geprüft, dass die
0029-Beschränkung vor dem Upgrade greift, nach dem Upgrade entfernt ist, beim
Downgrade wieder angelegt wird und vorhandene Bezeichnungen erhalten bleiben.

## Hinzugefügte Tests

Backend:

- Regressionstest für alle sieben von der Netzwerkseite verwendeten Endpunkte;
- Fallbacktests für alte oder unbekannte Netzwerk-Enum-Werte;
- Unterverteilung mit leerer und gefüllter Feldaufteilung;
- vollständiger Migrations-Rundlauf `0029 -> 0030 -> 0029 -> 0030`;
- Wikimedia-Timeout, HTTP-Fehler und nicht freigegebene Treffer-Hosts.

Frontend:

- Wikimedia-CORS-Suche, Hostfilter, Download und Ausfallfälle;
- Backend-zuerst- und Browser-Fallback-Vertrag der Produktbildkomponente;
- FIFO-Warteschlange, manuelles Schließen und unterschiedliche Anzeigedauer;
- globale Darstellung oberhalb von Dialogen;
- Verhalten des mobilen Zählerdialogs bei Erfolg und Fehler;
- Erreichbarkeit der Schrankaufteilung und leerer Zustand;
- fehlertolerantes Laden der Netzwerkseite.

Die Tests sind Bestandteil des Releases. Ihre vollständige Ausführung war in
dieser Umgebung aus den nachfolgend dokumentierten Gründen nicht möglich.

## Nicht vollständig ausführbare Prüfungen

### Backend-Testlauf

Der Aufruf

```text
python3 -m pytest backend/tests
```

endete beim Laden von `conftest.py` mit:

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

Ein Installationsversuch über die bereitgestellte Paketquelle schlug bereits
bei den Build-Abhängigkeiten mit einer nicht verfügbaren Paketquelle fehl. Ein
Versuch über die öffentliche PyPI-Adresse scheiterte an der DNS-Auflösung der
isolierten Umgebung. Deshalb konnten `pytest`, `ruff`, `mypy`, der vollständige
Alembic-Lauf und die Backend-API-Tests hier nicht vollständig ausgeführt werden.

### Frontend-Test und Build

Der korrekte Aufruf von `npm ci` im Verzeichnis `frontend` endete mit:

```text
npm error code E503
npm error 503 Service Temporarily Unavailable
```

Betroffen war der Download eines Pakets aus der bereitgestellten npm-Registry.
Dadurch standen `node_modules`, `vitest`, `vue-tsc`, Vite und die MDI-CSS-Datei
nicht vollständig zur Verfügung. Folgende Prüfungen konnten deshalb nicht
vollständig ausgeführt werden:

- `npm test`;
- `npm run build`;
- die vollständige MDI-Prüfung gegen `@mdi/font`;
- der produktive Vite-Build.

Als Ersatz wurden alle TypeScript- und Vue-Skriptblöcke syntaktisch geprüft und
der neu hinzugefügte browserseitige Wikimedia-Dienst mit dem vorhandenen
globalen TypeScript-Compiler streng geprüft. Dies ersetzt keinen vollständigen
Vue-/Vite-Build.

### Docker

`docker --version` endete mit `docker: command not found`. Daher waren

- `docker compose build`;
- Containerstart und Healthcheck;
- Prüfung der Backend-Logs im gebauten Image;
- praktische End-to-End-Tests im Browser

in dieser Umgebung nicht möglich.

## Performance- und Stabilitätsprüfung

Quellseitig geprüft und berücksichtigt wurden:

- Abbruch überholter Online-Suchen und Bildimporte;
- Zeitlimits für externe Suche, Download und Upload;
- kein dauerhafter externer Bildbezug nach Auswahl;
- kein vollständiger Ausfall der Netzwerkseite bei einem fehlerhaften
  Einzelendpunkt;
- keine zusätzliche Docker-, Datenbank- oder Worker-Architektur;
- keine neue Datenmigration außer der notwendigen Entfernung einer einzelnen
  Check-Constraint;
- keine Änderung an der neutralen Behandlung freier Switch-Ports;
- keine neuen blockierenden Schleifen oder periodischen Frontend-Requests in den
  geänderten Bereichen.

Eine belastbare Laufzeitmessung, SQL-Abfragezählung oder Browser-Profilierung war
ohne lauffähigen Gesamtbuild nicht möglich.

## Erforderliche Nachprüfung in einer vollständigen Build-Umgebung

Vor produktivem Einsatz sollten die CI-Schritte aus `.github/workflows/ci.yml`
ausgeführt werden:

```text
backend:  pip install -r requirements-dev.txt
          ruff check app tests
          mypy app
          python -m pytest -q
          alembic upgrade head

frontend: npm ci --ignore-scripts --no-audit --no-fund
          npm test
          npm run build

docker:   docker compose build
          docker compose up -d
          Healthcheck und Logs prüfen
```

Danach sind die vier gemeldeten Abläufe praktisch zu testen: Produktbildsuche
mit Backend und Browser-Fallback, Schrankaufteilung einer Unterverteilung,
Netzwerkseite mit vorhandenem Datenbestand sowie Zählerstandserfassung auf einem
kleinen Mobilbildschirm.

## Bewertung

Die vier Fehlerbereiche sind im Quellstand umgesetzt und durch statische
Prüfungen sowie eine eigenständige echte Migrationsprüfung abgesichert. Das
Release wird bewusst **nicht** als vollständig Docker- und End-to-End-validiert
bezeichnet, weil Paketquellen und Docker in der Ausführungsumgebung nicht
verfügbar waren.
