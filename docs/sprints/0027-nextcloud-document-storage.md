# Sprint 0027: Nextcloud-Dokumentenspeicher

- Status: Completed and operator-approved on 2026-07-22
- Target branch: `feature/nextcloud-document-storage`
- Depends on: Sprints 0001, 0002, 0009 und ADR-0006

> Dieses Dokument ist der vollständige Implementierungsvertrag für diesen Sprint. Zusätzlich gelten
> die verbindlichen Standards aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

Benutzer können einen fest eingegrenzten Nextcloud-Ordner als allgemeinen Dokumentenspeicher von
`docofhome` verwenden. Innerhalb dieses Stammordners können Dateien und Unterordner angezeigt,
angelegt, hochgeladen, heruntergeladen, umbenannt beziehungsweise verschoben und sicher gelöscht
werden. Die Nextcloud-Zugangsdaten und interne WebDAV-URL bleiben ausschließlich im Backend.

Der Sprint setzt den offenen Roadmap-Punkt „Nextcloud als allgemeiner verwalteter
Dokumentenspeicher“ um. Verknüpfungen der Dokumente mit Assets, Räumen oder Elektroobjekten gehören
bewusst nicht zu diesem Sprint und folgen in Sprint 0028.

## Hintergrund

Die bestehende Nextcloud-Integration wird bereits für optionale Backups verwendet. Für allgemeine
Hausdokumente fehlt jedoch eine von `docofhome` bedienbare, klar abgegrenzte Ablage. Dateien dürfen
nicht in SQLite kopiert und Nextcloud-Secrets dürfen nicht an den Browser übergeben werden.

Der Dokumentenspeicher ist eine ausdrücklich schreibende Integration. Der bestehende
Verbindungstest unter Einstellungen bleibt weiterhin schreibfrei; Schreibzugriffe entstehen nur
durch bewusste Aktionen auf der Dokumentenseite.

## Anforderungen

- Nextcloud bleibt optional; der lokale Kernbetrieb funktioniert ohne die Integration.
- Die Einstellungen erhalten einen Nextcloud-spezifischen Dokumenten-Stammordner.
- Standardwert für neue und migrierte Installationen ist `docofhome/Documents`.
- Der Stammordner ist relativ zum Nextcloud-Benutzerverzeichnis.
- Jeder Dokumentenzugriff ist technisch auf diesen Stammordner begrenzt.
- Absolute Pfade, `.`/`..`, Backslashes, Steuerzeichen, leere Segmente und überlange Segmente werden
  abgelehnt.
- Die Dokumenten-API gibt weder Nextcloud-URL noch Konto oder Secret aus. Die bestehende
  Einstellungs-API darf URL und Konto zur Bearbeitung anzeigen, gibt aber weiterhin niemals das
  gespeicherte Secret zurück.
- Der Browser kommuniziert ausschließlich mit `/api/v1/documents`.
- Ordnerinhalte werden über WebDAV `PROPFIND` mit Tiefe 1 geladen.
- Der fehlende Stammordner ist ein verständlicher leerer Erstzustand und kein Startfehler.
- Der Stammordner wird erst bei einer ausdrücklichen Schreibaktion angelegt.
- Ordner können im aktuellen Pfad angelegt werden.
- Dateien können mit ihrem ursprünglichen Dateinamen und Medientyp hochgeladen werden.
- Uploads und Downloads sind auf 100 MiB pro Datei begrenzt.
- Ein Upload überschreibt standardmäßig keine vorhandene Datei.
- Das Ersetzen einer vorhandenen Datei benötigt eine zweite ausdrückliche Benutzerbestätigung.
- Bei aktiviertem Nextcloud-Dateiversionsmodul kann Nextcloud frühere Versionen aufbewahren;
  `docofhome` verspricht oder verwaltet diese Versionshistorie in diesem Sprint nicht selbst.
- Dateien können über einen lokalen, durch das Backend geschützten Download-Endpunkt geladen werden.
- Dateien und Ordner können ohne Überschreiben eines vorhandenen Ziels umbenannt oder verschoben
  werden.
- Der Stammordner selbst kann nicht umbenannt, verschoben oder gelöscht werden.
- Dateien können nach Bestätigung gelöscht werden.
- Ordner können nur gelöscht werden, wenn sie leer sind. Die Löschung verwendet den zuvor
  verifizierten ETag als Bedingung; rekursives Löschen ist nicht erlaubt.
- Verbindungs-, Berechtigungs- und Konfliktfehler werden verständlich angezeigt, ohne interne
  Credentials oder vollständige Remote-Antworten offenzulegen.
- Die Dokumentenseite bleibt auf Desktop und Mobilgeräten bedienbar und unterstützt Dark/Light Mode.

## Backend

### Persistente Konfiguration

Die bestehende Tabelle `integration_settings` erhält additiv:

- `document_root`: nullable String bis 500 Zeichen

Das Feld ist nur für die Integration `nextcloud` zulässig. Beim Upgrade wird für vorhandene
Nextcloud-Einstellungen ohne Wert `docofhome/Documents` gesetzt. Andere Integrationen behalten
`NULL`.

### Connector

Ein neuer `NextcloudWebDavConnector` kapselt:

- Konto-basierte Basic-Auth mit dem gespeicherten App-Passwort beziehungsweise Token
- Konstruktion sicher URL-kodierter WebDAV-Pfade
- `PROPFIND`, `MKCOL`, `PUT`, `GET`, `MOVE` und `DELETE`
- deaktivierte Redirect-Folge
- begrenzte Timeouts
- Prüfung, dass zurückgelieferte WebDAV-Hrefs zum konfigurierten Benutzerbereich gehören

Der Connector kennt keine HTTP-API-Schemas und gibt keine Secrets zurück.

### Service

Der `DocumentService` besitzt:

- Validierung relativer Pfade und Namen
- Auflösung der Nextcloud-Konfiguration
- Begrenzung auf den konfigurierten Stammordner
- Parsing und Sortierung der WebDAV-Multistatus-Antworten
- Ordner-vor-Dateien-Sortierung, danach stabil nach sichtbarem Namen
- explizite Konfliktbehandlung ohne Standardüberschreiben
- Größenlimits für Upload und Download
- Schutz vor rekursivem Löschen
- Schutz vor Verschieben eines Ordners in sich selbst
- sichere, domänenspezifische Fehlerklassen

### API

Neue Endpunkte unter `/api/v1/documents`:

```text
GET    /api/v1/documents?path=<relative-path>
POST   /api/v1/documents/folders
POST   /api/v1/documents/upload?path=<folder>&filename=<name>&overwrite=false
GET    /api/v1/documents/download?path=<file>
POST   /api/v1/documents/move
DELETE /api/v1/documents?path=<entry>
```

Antworten enthalten ausschließlich:

- relativen Pfad innerhalb des Stammordners
- sichtbaren Namen
- Typ `file` oder `folder`
- Größe
- optionale Änderungszeit
- optionalen Medientyp und ETag
- Mutationsstatus wie `created` oder `overwritten`

Fehlerzuordnung:

- unvollständige/deaktivierte Nextcloud-Konfiguration: HTTP 409
- ungültiger Pfad oder unzulässige Operation: HTTP 422
- fehlender Eintrag: HTTP 404
- Namens-, Ziel- oder Löschkonflikt: HTTP 409
- Größenlimit: HTTP 413
- Nextcloud nicht erreichbar oder unerwartete WebDAV-Antwort: HTTP 502

## Frontend

- Neuer Navigationspunkt **Dokumente** unter `/documents`.
- Bei deaktivierter oder unvollständiger Integration erscheint ein klarer Hinweis mit Link zu den
  Einstellungen.
- Der konfigurierte Stammordner wird sichtbar, aber ohne Server-URL oder Kontodaten angezeigt.
- Breadcrumbs navigieren durch Unterordner.
- Der aktuelle Ordner kann lokal nach Name oder Medientyp gefiltert werden.
- Ordner werden vor Dateien angezeigt.
- Dateien zeigen Name, Größe, Änderungszeit und Medientyp.
- Geeignete MDI-Symbole unterscheiden Ordner, PDF, Bild, Tabelle, Text und allgemeine Dateien.
- Aktionen: Ordner anlegen, Datei hochladen, aktualisieren, herunterladen, umbenennen, verschieben und löschen.
- Beim Verschieben wird der Zielordner über einen lazy geladenen Ordnerbaum gewählt; das freie
  Eingeben interner Pfade ist nicht erforderlich. Der aktuelle Ordner ist vorausgewählt und ein
  Ordner selbst sowie seine Unterordner sind als unzulässige Ziele gesperrt.
- Ein Namenskonflikt beim Upload öffnet einen ausdrücklichen Ersetzen-Dialog.
- Nicht leere Ordner erklären, warum sie nicht gelöscht werden können.
- Lade-, Leer-, Erstordner-, Erfolg-, Konflikt- und Fehlerzustände sind unterscheidbar.
- Keine direkte Nextcloud-URL wird als Link oder Fetch-Ziel erzeugt.

## Migrationen

Neue additive Migration:

- `0017_add_nextcloud_document_root.py`

Upgrade:

- ergänzt `integration_settings.document_root`
- setzt den Standard nur für bereits vorhandene Nextcloud-Zeilen ohne Wert
- erhält IDs, URL, Konto, Secret, Albumauswahl und Zeitstempel

Downgrade:

- entfernt ausschließlich `document_root`
- erhält die übrige Integrationseinstellung

## Tests

Backend Service/Connector:

- Stammordner und Unterordner werden korrekt URL-kodiert und begrenzt.
- WebDAV-Listen werden in Datei-/Ordnerverträge geparst und stabil sortiert.
- ein fehlender Stammordner erzeugt einen leeren Erstzustand.
- Ordneranlage erstellt benötigte Stammordner nur bei der ausdrücklichen Aktion.
- Upload verwendet ohne Bestätigung `If-None-Match: *`.
- Konflikte benötigen einen zweiten Upload mit `overwrite=true`.
- Medientypen und Bytes werden unverändert an Nextcloud übertragen.
- Uploads und Downloads über 100 MiB werden abgelehnt.
- Downloads laufen ausschließlich über die lokale API.
- `MOVE` setzt `Overwrite: F`.
- Pfadtraversal, Backslash, absolute Pfade und Steuerzeichen werden vor einem Remotezugriff abgelehnt.
- nicht leere Ordner werden nicht an WebDAV `DELETE` weitergereicht; leere Ordner werden mit
  `If-Match` auf ihren verifizierten ETag gelöscht.
- deaktivierte oder unvollständige Integration erzeugt keinen Remotezugriff.

Backend API:

- Listen-, Upload-, Download-, Move- und Delete-Verträge
- sichere Statuscodes für Konfiguration, Validierung, Not Found, Konflikt, Größe und Remoteausfall
- Content-Disposition für Unicode-Dateinamen
- `nosniff` beim Download
- keine Nextcloud-URL, kein Konto und kein Secret in Antworten der Dokumenten-API

Migration und Einstellungen:

- Upgrade von 0016 setzt den Standard und erhält bestehende Konfiguration.
- Downgrade auf 0016 erhält URL und Konto.
- Dokumenten-Stammordner wird normalisiert und nur für Nextcloud akzeptiert.
- API-Antworten redigieren weiterhin das Secret.

Frontend/Vitest:

- Der Zielordnerbaum erzeugt die benötigte Stamm-zu-Ziel-Pfadkette und sperrt Selbst-/Unterordnerziele.
- Pfade und Unicode werden korrekt an die lokale API serialisiert.
- Upload sendet den `File`-Body und kein Secret.
- `overwrite=true` wird nur nach ausdrücklicher Auswahl gesetzt.
- lokaler Downloadpfad wird korrekt erzeugt.
- MOVE- und DELETE-Verträge sind typisiert.
- Konfliktfehler bleiben für den Ersetzen-Dialog erkennbar.
- Nextcloud-Dokumentenpfad wird nur bei Nextcloud gespeichert.

Required static, build, and Docker checks:

- Ruff
- mypy
- pytest
- Alembic Upgrade, Downgrade und `alembic check`
- Vitest
- vue-tsc
- Vite production build
- MDI-Iconprüfung
- Docker build

## Explizit nicht Teil dieses Sprints

- Verknüpfung von Dokumenten mit Assets, Räumen, Verteilungen, Schutzgeräten oder Stromkreisen
- lokale Dokumentmetadaten oder Volltextindex in SQLite
- globale Suche in Nextcloud-Dokumenten
- Nextcloud-Freigaben, öffentliche Links, Kommentare oder Tags
- Anzeige oder Wiederherstellung früherer Nextcloud-Dateiversionen
- rekursives Löschen von Ordnern
- Datei-Vorschau beziehungsweise Office-Bearbeitung im Browser
- Synchronisierung für Offlinekopien
- Mehrbenutzerrechte innerhalb von `docofhome`

## Implementierungsstand

Im Paket `0.1.11-dev` lokal umgesetzt:

- persistenter, Nextcloud-spezifischer Dokumenten-Stammordner mit Migration `0017`
- sicherer WebDAV-Connector und Dokumentservice
- versionierte Dokumenten-API mit Liste, Ordner, Upload, Download, Move/Rename und Delete
- 100-MiB-Grenzen, kein Standardüberschreiben, kein rekursives Löschen
- responsive Dokumentenseite mit Umbenennen und echtem Verschieben sowie Einstellungen im Setup
  und im laufenden System
- Backend-, API-, Migrations- und Frontend-Vertragstests
- Projektstatus, Roadmap, README, ADR und Changelog aktualisiert

Lokal in der Chat-Umgebung bestätigt:

- Python-Compileall und AST-Parsing für Backend, Tests und Migrationen
- Migration `0017` als reales SQLite-Upgrade und -Downgrade über Alembic Operations
- WebDAV-Connector- und Dokumentservice-Verträge mit `httpx.MockTransport`
- Pydantic-Verträge für Dokumentwurzel, Konto und Secret-Isolation
- TypeScript-Syntaxtranspilation für alle `.ts`-Dateien und Vue-`script setup`-Blöcke
- strikte TypeScript-Prüfung und ausführbare Laufzeitverträge für die neue Dokumenten-API
- Tag-Balance der Dokumentenseite, interne Markdown-Links, relative Frontend-Importe, Versions- und
  Migrationskonsistenz

## Abnahmeprotokoll

- Die produktive Frontend-Erstellung im Zielsystem wurde nach der Korrektur des nicht verfügbaren
  MDI-Icons und des erweiterten `IntegrationRead`-Testfixtures erfolgreich bis zur nutzbaren
  Anwendung fortgeführt.
- Die Nextcloud-Dokumentenverwaltung wurde im Zielsystem praktisch verwendet; die nachträglich
  gewünschte baumgestützte Zielordnerauswahl ist Bestandteil des freigegebenen Stands.
- Der Betreiber hat Sprint 0027 am **22. Juli 2026** ausdrücklich freigegeben.
- Vollständige kombinierte Protokolle aller Ruff-, mypy-, Pytest-, Vitest- und Docker-Gates sind in
  dieser Chat-Umgebung nicht archiviert. Dies bleibt eine allgemeine CI-/Stabilisierungsempfehlung,
  ist nach der ausdrücklichen Betreiberfreigabe jedoch kein offener Abnahmepunkt dieses Sprints.

## Definition of Done

- [x] Der Dokumenten-Stammordner ist persistent und update-sicher.
- [x] Jeder Remotezugriff bleibt unter diesem Stammordner.
- [x] Die Dokumenten-API enthält weder Nextcloud-URL noch Konto oder Secret.
- [x] Ordner, Upload, Download, Rename/Move und sicheres Delete sind umgesetzt.
- [x] Überschreiben benötigt eine ausdrückliche zweite Aktion.
- [x] Nicht leere Ordner können nicht rekursiv gelöscht werden; leere Ordner sind per ETag gegen
  zwischenzeitliche Änderungen abgesichert.
- [x] Größen- und Pfadgrenzen sind implementiert.
- [x] Dokumentenoberfläche ist responsive angelegt.
- [x] Sprint 0028 wurde nicht vorweggenommen.
- [x] Zielsystem-Buildfehler für MDI-Icon und TypeScript-Testfixture sind behoben.
- [x] Die praktische Nextcloud-Nutzung und die baumgestützte Ordnerauswahl sind dokumentiert.
- [x] Der Betreiber hat den vollständigen Sprintstand ausdrücklich freigegeben.
