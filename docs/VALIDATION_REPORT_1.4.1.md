# Validierungsbericht DocOfHome 1.4.1

Stand: 25. Juli 2026  
Ausgangsbasis: DocOfHome 1.4.0  
Zielversion: DocOfHome 1.4.1  
Alembic-Head: `0035`

## 1. Umgesetzter Umfang

- zentrale Seite **Mehr → Über DocOfHome**;
- Projektbeschreibung und Hinweis auf lokale Datenhoheit;
- installierte Version aus der zentralen Backend-Versionsquelle;
- aus den ausgelieferten `RELEASE_NOTES_*.md`-Dateien geladene
  Versionshistorie;
- sichere, bewusst begrenzte Markdown-Darstellung ohne `v-html`;
- optionale Projekt-, Repository-, Release- und Issue-Verweise;
- optionaler Lizenzhinweis;
- konfigurierbares, im Standardzustand leeres Impressum;
- standardmäßig deaktiviertes Feedbackformular;
- ausdrückliche Zustimmung vor Übertragung technischer Metadaten;
- serverseitiger Feedback-Upload in einen validierten Nextcloud-Zielordner,
  ohne WebDAV-Zugangsdaten im Browser;
- serverseitig erzeugte Dateinamen, Größenlimits, Kategorien und einfaches
  Rate-Limit;
- Versionskachel vom Dashboard entfernt;
- direkter Dashboard-Button **Zählerstände erfassen**;
- automatische Bereinigung alter Dashboard-Layouts unter Erhalt von
  Reihenfolge und Sichtbarkeit der übrigen Kacheln;
- Migration `0035_about_page_and_feedback`.

## 2. Tatsächlich erfolgreich ausgeführte Prüfungen

### Quellstand und Versionen

- `python scripts/check-version.py`;
- statische Releaseverträge für 1.2.4, 1.3.0, 1.3.1, 1.3.2, 1.4.0 und 1.4.1;
- Versionsabgleich von `VERSION`, Backend, Frontend und Lockdatei;
- Python-Zeilenlängenprüfung der für 1.4.1 geänderten Dateien.

### Python und Datenverträge

- `python -m compileall -q backend/app backend/migrations backend/tests scripts`;
- Pydantic-Prüfung der Projekt-, Impressums- und Feedbackkonfiguration;
- Ablehnung leerer beziehungsweise nur aus Leerzeichen bestehender
  Pflichtangaben;
- Prüfung des validierten Nextcloud-Zielordners;
- Prüfung, dass technische Metadaten nur nach ausdrücklicher Zustimmung
  akzeptiert werden.

### Migrationen

Die eigenständigen Migrationsprüfungen für `0030` bis `0035` wurden ausgeführt.
Für Migration `0035` wurden Upgrade, Downgrade und erneutes Upgrade auf einer
repräsentativen SQLite-Ausgangsdatenbank erfolgreich geprüft. Dabei wurden die
neuen optionalen Projekt-, Impressums- und Feedbackfelder angelegt und beim
Downgrade wieder entfernt.

### Frontend-Quellstruktur

- TypeScript-Syntax aller `.ts`-Dateien und der TypeScript-Scriptblöcke aller
  Vue-Komponenten mit dem lokal vorhandenen TypeScript-Parser;
- strukturelle Prüfung der geänderten Vue-Templates auf ausgeglichene Tags;
- statische Regressionstests für Info-Seite, sichere Markdown-Ausgabe und
  direkten Zählerstandseinstieg wurden in den Quellstand aufgenommen.

### Releasepaket

Nach der finalen Paketierung wurde das ZIP in einen neuen Ordner entpackt. Alle
Manifestdateien wurden anhand von relativem Pfad, Dateigröße und SHA-256 erneut
geprüft. Die statischen Versions-, Release- und Migrationsprüfungen wurden aus
dem entpackten Releasebestand erneut ausgeführt.

## 3. Aufgenommene Regressionstests

Neu beziehungsweise erweitert wurden Tests für:

- zentrale Version, Release-Historie und leeres Impressum;
- explizite Zustimmung für technische Feedbackinformationen;
- sichere Feedbackdatei und serverseitig erzeugten Dateinamen;
- standardmäßig deaktiviertes Feedback;
- Upgrade und Downgrade der Migration `0035`;
- Entfernen der historischen Dashboard-Versionskachel ohne Verlust der
  gespeicherten Kachelreihenfolge;
- Info-API und minimierte Feedbackdaten;
- Info-Seite ohne ausführbares HTML;
- direkten Aufruf des Zählerstandsdialogs vom Dashboard.

## 4. Nicht vollständig ausführbare Prüfungen

### Frontend

`npm ci` konnte in der Arbeitsumgebung wegen nicht erreichbarer Paketquellen
nicht abgeschlossen werden. Deshalb werden Vitest, `vue-tsc --noEmit`, die
MDI-Prüfung und der vollständige Vite-Build nicht als bestanden behauptet. Die
Syntax- und Strukturprüfungen ersetzen keinen vollständigen Frontend-Build.

### Backend

Die vollständigen Entwicklungsabhängigkeiten, insbesondere `sqlmodel`, Ruff und
mypy, waren in der Arbeitsumgebung nicht verfügbar und konnten wegen fehlender
Namensauflösung nicht nachinstalliert werden. Deshalb werden der vollständige
Pytest-, Ruff- und mypy-Lauf nicht als bestanden behauptet. Python-Syntax,
Pydantic-Verträge und die eigenständigen Alembic-/SQLAlchemy-Migrationsprüfungen
wurden tatsächlich ausgeführt.

### Docker

Docker oder Podman steht in der Arbeitsumgebung nicht zur Verfügung. Image-Build,
Containerstart, Healthcheck und praktische Browserprüfung müssen auf dem
Zielsystem erfolgen.

## 5. Empfohlene Zielsystemprüfung

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=200
```

Danach prüfen:

1. Alembic aktualisiert ohne Fehler auf Head `0035`.
2. **Mehr → Über DocOfHome** öffnet ohne Fehler.
3. Die Seite zeigt Version `1.4.1` und die Release-Historie.
4. Leere Projektlinks und ein leeres Impressum bleiben ausgeblendet.
5. Nach Pflege in den Einstellungen erscheinen nur die gesetzten Angaben.
6. Feedback bleibt standardmäßig unsichtbar beziehungsweise deaktiviert.
7. Bei aktivierter Nextcloud-Integration wird Feedback als Markdown-Datei im
   konfigurierten Ordner gespeichert.
8. Ohne Zustimmung werden keine technischen Metadaten übertragen.
9. Die Versionskachel ist vom Dashboard entfernt.
10. **Zählerstände erfassen** öffnet auf dem Smartphone direkt den
    Ablesedialog.
11. Ein zuvor individuell sortiertes Dashboard behält nach der Bereinigung die
    Reihenfolge und Sichtbarkeit seiner verbleibenden Kacheln.
12. Bestehende Elektro-, Verbrauchs-, Asset- und Integrationsdaten bleiben
    unverändert vorhanden.

## 6. Bewertung

Der vereinbarte Funktionsumfang ist im Quellstand umgesetzt. Versionen,
Migrationen, Quellsyntax, Datenvalidierung und Release-Roundtrip wurden geprüft.
Die produktive Freigabe bleibt vom vollständigen npm-/Backend-/Docker-Lauf und
der praktischen Prüfung auf dem NAS abhängig.
