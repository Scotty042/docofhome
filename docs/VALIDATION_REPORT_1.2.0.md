# Validierungsbericht DocOfHome 1.2.0

Stand: 23.07.2026  
Ausgangsbasis: DocOfHome 1.1.3  
Alembic-Head: `0029`

## Ergebnisübersicht

DocOfHome 1.2.0 wurde aus dem freigegebenen Stand 1.1.3 erstellt. Die neuen
Datenbankänderungen, Python- und TypeScript-Syntax, Versionsangaben, bestehende
Projektprüfungen sowie das Releasepaket wurden geprüft. Vollständige Backend-
und Frontend-Testläufe waren in der isolierten Build-Umgebung nicht möglich,
weil die Ausgangs-ZIP keine installierten Abhängigkeiten enthält und der
Paketserver nicht erreichbar war. Nicht ausgeführte Prüfungen werden daher
nicht als bestanden ausgewiesen.

## Umgesetzte Funktionsbereiche

- Home-Assistant-Seite mit echter serverseitiger Pagination, serverseitigen
  Filtern, verzögertem Laden und dauerhaftem Mehrfachauswahlzustand.
- Gebündelter Home-Assistant-Abgleich mit Single-Flight-Sperre, 15 Minuten
  Registercache und 30 Sekunden Livezustandscache.
- Mehrere HA-Geräte und HA-Entitäten pro Asset einschließlich Entitätsrollen.
- Allgemeine DIN-Hutschienengeräte mit TE-Breite, Platzierung und Livewerten.
- N- und PE-Schienen auf derselben Ebene mit eindeutiger Seite links/rechts.
- Produktbild-Upload, Immich-Auswahl, kontrollierbare Wikimedia-Suche,
  manueller URL-Eingabe, Vorschau und Entfernen.
- Asset-Duplizierung und Serienanlage mit optionaler fortlaufender Platzierung.
- Inline-Anlage von Labels im Asset-Formular.
- Aufklappbare Navigation „Mehr“.
- Gzip-Komprimierung größerer Antworten und Reduktion mehrerer N+1-Abfragen.

## Tatsächlich ausgeführte Prüfungen

### Python und Projektverträge

| Prüfung | Ergebnis |
|---|---|
| `python3 -m compileall -q backend/app backend/migrations/versions backend/tests scripts` | Bestanden |
| `python3 scripts/check-version.py` | Bestanden, alle Versionsquellen `1.2.0` |
| `python3 scripts/check-branding.py` | Bestanden |
| `python3 scripts/check-collected-fixes.py` | Bestanden, 10/10 Verträge vorhanden |
| `python3 scripts/check-reading-reminders.py` | Bestanden |
| `git diff --check` | Bestanden |
| Suche nach `mdi-ground-wire` in produktivem Quellcode | Kein Treffer |
| Pydantic-Vertragsprüfungen für DIN-Produkte, Bereichsseiten, Serienplatzierung und primäre HA-Rolle | Bestanden |

### Migrationen

Die Migration wurde mit Alembics `MigrationContext` und `Operations` direkt
gegen temporäre SQLite-Datenbanken ausgeführt. Dadurch konnte die eigentliche
DDL- und Datenmigration unabhängig von der nicht verfügbaren SQLModel-
Laufzeit geprüft werden.

| Kette | Ergebnis |
|---|---|
| Leere Datenbank → Migration 0029 | Bestanden |
| Bestehender Stand 0028 → 0029 | Bestanden |
| 0029 → 0028 | Bestanden |
| 0028 → 0029 erneut | Bestanden |

Zusätzlich geprüft:

- Neue Produktfelder und die Einstellung für die Online-Bildsuche werden angelegt.
- Bestehende HA-Zuordnungen erhalten die Rolle `additional`.
- Bestehende halbe Schrankbereiche werden verlustfrei auf `links` migriert.
- Eine rechte Hälfte auf derselben Ebene kann danach angelegt werden.
- Doppelte linke/rechte Belegungen und Überdeckung durch volle Bereiche werden
  durch Constraints beziehungsweise Trigger verhindert.
- Beim Downgrade werden kollidierende Ebenen vor Entfernung des Seitenfelds auf
  eindeutige Positionen verschoben, sodass beide Bereiche erhalten bleiben.
- Die Tabelle für allgemeine DIN-Asset-Platzierungen wird korrekt angelegt und
  beim Downgrade entfernt.

### Frontend-Syntax

Mit dem global vorhandenen TypeScript-Parser wurden alle `.ts`-Dateien und
alle TypeScript-Skriptblöcke der Vue-Komponenten eingelesen.

- Geprüfte Dateien/Skriptblöcke: 150
- Parserfehler: 0

### Releaseprüfung

Die endgültige Release-ZIP wurde mit reproduzierbarer Dateireihenfolge und
festen ZIP-Zeitstempeln erzeugt und anschließend unabhängig erneut entpackt.

- Projektdateien im Manifest: 491
- Dateien im ZIP einschließlich `RELEASE_MANIFEST.txt`: 492
- `.git`, `node_modules`, `__pycache__`, `.pytest_cache`, Build-Caches,
  temporäre Datenbanken und echte `.env`-Dateien: nicht enthalten
- Interne Manifestdatei mit SHA-256 und Dateigröße jeder Projektdatei: geprüft
- Externe Manifestkopie: identisch mit der internen Manifestdatei
- Externe SHA-256-Prüfsumme des ZIP-Archivs: erzeugt und gegengeprüft
- ZIP-CRC-Prüfung: bestanden
- Jede Manifestzeile gegen die unabhängig entpackte Datei: bestanden
- Zusätzliche oder fehlende Projektdateien gegenüber dem Manifest: keine

## Ergänzte Regressionstests

Folgende automatisierte Tests wurden dem Projekt hinzugefügt oder erweitert:

- HA-Mehrfachzuordnung, Rollen und Konfliktschutz.
- Pagination und Filterung mit 5.000 simulierten HA-Entitäten.
- Single-Flight-Verhalten bei parallelen HA-Synchronisierungen.
- Asset-Duplikate und Serien ohne Übernahme eindeutiger Kennungen.
- N-/PE-Seitenkonflikte und volle Bereiche.
- Allgemeine DIN-Platzierung und Produkt-TE-Breite.
- Produktbildsignaturen und Einschränkung des Online-Imports auf Wikimedia.

Diese Tests sind Bestandteil des Releases, konnten in dieser Umgebung jedoch
nicht vollständig ausgeführt werden.

## Nicht ausführbare Prüfungen

### Pytest, Ruff und Mypy

- `pytest -q` wurde gestartet, brach aber bereits beim Laden von `conftest.py`
  mit `ModuleNotFoundError: No module named 'sqlmodel'` ab.
- Ein Installationsversuch für `sqlmodel` scheiterte, weil der konfigurierte
  Paketserver in der isolierten Umgebung nicht erreichbar war.
- `ruff` und `mypy` sind in der Umgebung nicht installiert.

Daher gibt es keinen behaupteten vollständigen Backend-Test-, Ruff- oder
Mypy-Erfolg. Die Python-Kompilierung und die direkten Migrationsprüfungen sind
bestanden.

### NPM-Test und Produktionsbuild

- `npm ci --offline --ignore-scripts` scheiterte, weil benötigte Pakete nicht im
  lokalen NPM-Cache vorhanden waren.
- `npm run build` wurde gestartet, konnte aber ohne `node_modules` bereits bei
  der MDI-CSS-Prüfung nicht fortfahren.
- Der TypeScript-Parserlauf ersetzt keine vollständige `vue-tsc`-, Vitest- oder
  Vite-Buildprüfung.

Daher gibt es keinen behaupteten vollständigen Frontend-Test oder
Produktionsbuild.

### Docker-Build

Docker ist in der Ausführungsumgebung nicht installiert. Ein Docker-Build
konnte nicht ausgeführt werden.

## Performancebewertung

Die Hauptursache der langsamen HA-Seite in 1.1.3 war nicht nur die Datenmenge,
sondern dass das Frontend paginierte Antworten bis zur letzten Seite erneut
zusammenführte und anschließend alle Entitäten renderte. Zusätzlich konnte ein
manueller Refresh über mehrere API-Aufrufe mehrere vollständige Abgleiche
anstoßen.

In 1.2.0 gilt:

- Geräte: standardmäßig 50 Datensätze je API-Seite.
- Entitäten: standardmäßig 100 Datensätze je API-Seite.
- Entitäten werden erst beim Öffnen des Bereichs, bei einer Suche oder für ein
  ausgewähltes Gerät geladen.
- Suche, Bereich, Domain, Gerät, Geräteklasse, Einheit und Verfügbarkeit werden
  im Backend gefiltert.
- „Nur ausgewählte Entitäten“ lädt nur die ausgewählten Datensätze.
- Ein Refresh stößt nur einen gebündelten Abgleich an; parallele Anforderungen
  warten auf denselben Lauf.
- Registerdaten und Livezustände besitzen getrennte Cachezeiten.
- Mehrere Asset-, Platzierungs- und Livewertansichten verwenden gebündelte
  Datenbankabfragen statt wiederholter Einzelabfragen.

Ein reproduzierbarer Browser-Lauf mit einem realen Home-Assistant-System und
5.000 Entitäten war in dieser Umgebung nicht möglich. Der enthaltene Testfall
für 5.000 Entitäten muss nach Installation der Projektabhängigkeiten in CI oder
auf dem Zielsystem ausgeführt werden.

## Empfohlene Zielsystemprüfung vor produktivem Rollout

1. Sicherung der produktiven Datenbank und des Datenverzeichnisses erstellen.
2. Release zunächst in einer Testinstanz mit einer Kopie der Datenbank starten.
3. Migration auf 0029 prüfen und N-/PE-Bereiche visuell kontrollieren.
4. HA-Seite mit dem realen System öffnen, suchen, Seiten wechseln und einen
   manuellen Refresh ausführen.
5. Mehrfachzuordnungen, Livewerte, Produktbilder und Serienanlage mit wenigen
   Beispieldatensätzen prüfen.
6. Danach erst das produktive Update durchführen.

## Gesamturteil

Der Quellstand ist statisch konsistent, die Datenbankmigration einschließlich
Upgrade-/Downgrade-Zyklus ist praktisch geprüft und die Releaseartefakte wurden
gegen ihr Manifest validiert. Wegen der nicht verfügbaren Python- und
Node-Abhängigkeiten bleibt der vollständige automatisierte Anwendungs-,
Frontend- und Docker-Build als Zielsystem-/CI-Prüfung offen.
