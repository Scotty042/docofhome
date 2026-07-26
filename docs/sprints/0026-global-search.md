# Sprint 0026: Globale Suche

- Status: Implemented locally; final quality-gate acceptance pending
- Target branch: `feature/global-search`
- Depends on: Sprints 0004, 0005, 0019, 0022, 0024 und 0025

> Dieses Dokument ist der vollständige Implementierungsvertrag für diesen Sprint. Zusätzlich gelten
> die verbindlichen Standards aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

Benutzer können aus der normalen docofhome-App heraus lokale dokumentierte Objekte über ein
zentrales Suchfeld finden und direkt öffnen. Die Suche umfasst Assets, Bereiche und Räume,
Verteilungen, Schutzgeräte und Stromkreise, ohne dass zuvor das jeweilige Modul geöffnet werden
muss.

Der Sprint schließt den noch offenen Punkt „Global live search“ aus Roadmap 0.2 ab.

## Hintergrund

docofhome besitzt bereits modulbezogene Listen und Suchparameter. Mit wachsendem Datenbestand ist
jedoch unklar, in welchem Modul ein gesuchtes Gerät, ein Raum, eine Verteilung oder ein Stromkreis
abgelegt ist. Eine zentrale Suche fehlt.

Die Suche bleibt vollständig lokal und greift nicht direkt auf Home Assistant, Immich oder
Nextcloud zu. Sie verwendet die vorhandenen lokalen Tabellen, stabilen UUIDs und bestehenden
Detail- beziehungsweise Editorrouten.

## Anforderungen

- In der normalen App-Leiste steht eine globale Suche zur Verfügung.
- Die Suche startet erst nach mindestens zwei sichtbaren Zeichen.
- Führende und nachfolgende Leerzeichen werden entfernt.
- Suchtexte sind auf 100 Zeichen begrenzt.
- Die Suche ist ohne Beachtung der Groß- und Kleinschreibung möglich.
- `%`, `_` und andere SQL-Wildcards aus Benutzereingaben werden als normale Zeichen behandelt.
- Ergebnisse werden nach Objekttyp gruppiert.
- Pro Objekttyp werden standardmäßig höchstens fünf Ergebnisse zurückgegeben.
- Der Client darf ein Limit zwischen 1 und 20 Ergebnissen pro Typ anfordern.
- Standardmäßig werden nur aktive, nicht archivierte Datensätze berücksichtigt.
- Ein optionaler API-Parameter darf archivierte lokale Datensätze einbeziehen; die erste
  Frontendausbaustufe verwendet ihn nicht.
- Eine exakte Übereinstimmung mit Code oder Nummer wird vor Präfix- und Teiltreffern sortiert.
- Danach erfolgt eine stabile Sortierung nach sichtbarem Titel und UUID.
- Jede Ergebniszeile enthält eine verständliche Kategorie, einen Titel, einen Kontexttext und ein
  lokales Navigationsziel.
- Leere, zu kurze und nicht erfolgreiche Suchen erzeugen verständliche, unterschiedliche Zustände.
- Fehler eines einzelnen Suchbereichs dürfen nicht als scheinbar vollständiges Gesamtergebnis
  ausgegeben werden. Die API antwortet in diesem Fall mit einem Fehler.
- Es werden keine Secrets, internen Integrations-URLs oder externen Rohdaten in Suchergebnisse
  aufgenommen.
- Die Suche bleibt offline nutzbar und benötigt keine konfigurierte Integration.

### Durchsuchte lokale Inhalte

Assets:

- Name
- docofhome-Code aus dem kompatiblen Feld `jarvis_code`
- Beschreibung
- Seriennummer
- Inventarnummer
- Asset-Typ
- Produktname
- Hersteller
- Modellnummer
- zugeordneter Standortpfad

Bereiche und Räume:

- Name
- Kurzname
- Beschreibung
- Notizen
- vollständiger hierarchischer Pfad

Verteilungen:

- Bezeichnung
- Name und Code des zugrunde liegenden Assets
- Beschreibung
- Notizen
- Standortpfad

Schutzgeräte:

- Name und Code des zugrunde liegenden Assets
- Gerätetyp
- Beschreibung
- Notizen
- zugehörige Verteilung
- vorhandene technische Kennwerte nur als Kontext, nicht als eigenständige numerische Volltextsuche

Stromkreise:

- Name
- Stromkreisnummer
- Beschreibung
- Notizen
- zugehörige Verteilung
- zugeordnetes Schutzgerät

## Backend

### API

Neuer versionierter Endpunkt:

```text
GET /api/v1/search
```

Query-Parameter:

- `q`: erforderlich, nach Trim 2 bis 100 Zeichen
- `limit_per_type`: optional, Standard 5, Minimum 1, Maximum 20
- `include_archived`: optional, Standard `false`

Die Antwort enthält:

- den normalisierten Suchtext
- die Gesamtzahl der zurückgegebenen Treffer
- eine feste Liste von Ergebnisgruppen
- für jede Gruppe Typ, sichtbare Bezeichnung, Trefferzahl und Ergebnisliste

Jedes Ergebnis besitzt mindestens:

- `result_type`: `asset`, `location`, `electrical_distribution`,
  `electrical_protective_device` oder `electrical_circuit`
- `id`: stabile UUID des Zielobjekts
- `title`: primäre sichtbare Bezeichnung
- `subtitle`: knapper Objektkontext
- `description`: optionaler zusätzlicher Trefferkontext
- `route`: ausschließlich ein lokaler Frontendpfad
- `archived`: boolescher Status
- `matched_fields`: allow-list-basierte sichtbare Feldbezeichnungen, keine internen SQL-Ausdrücke

Lokale Ziele:

- Asset: `/assets/{id}`
- Bereich oder Raum: `/locations/{id}`
- Verteilung: `/electrical/distributions/{id}`
- Schutzgerät: `/electrical/protective-devices/{id}/edit`
- Stromkreis: `/electrical/circuits/{id}`

Archivierte Ziele erhalten nur bei `include_archived=true` den bereits etablierten
`archived=1`-Queryparameter, sofern die Zielseite diesen unterstützt. Für Objekttypen ohne sicheren
historischen Leseweg werden keine archivierten Ergebnisse zurückgegeben.

### Architektur

- Ein neues Suchmodul besitzt API-Schemas, Service und Tests.
- Der Router validiert Parameter, ruft den Service auf und bildet bekannte Fehler auf HTTP-Antworten
  ab.
- Der Search-Service aggregiert die Ergebnisse der bestehenden Modul-Repositories.
- Suchlogik wird nicht in den Router und nicht in das Frontend dupliziert.
- Modul-Repositories behalten die Verantwortung für ihre Tabellen, Joins, Soft-Delete-Sichtbarkeit,
  Escaping, Ranking und stabile Sortierung.
- Der Service öffnet keine eigenen globalen Datenbanksessions außerhalb der bestehenden Dependency
  Injection.
- Es wird keine externe Suchmaschine und kein externer Index eingeführt.
- Für diesen Sprint wird keine SQLite-FTS-Tabelle angelegt. Die vorhandenen Datenmengen und
  begrenzten Trefferlisten werden über sichere lokale Abfragen bedient.
- Die Antwort ist vollständig typisiert und enthält keine ORM- oder Persistenzmodelle direkt.

### Fehlerverhalten

- fehlendes `q`: HTTP 422
- weniger als zwei Zeichen nach Trim: HTTP 422
- mehr als 100 Zeichen: HTTP 422
- ungültiges Limit: HTTP 422
- Datenbank- oder Servicefehler: bestehendes sicheres API-Fehlermuster ohne SQL-, Pfad- oder
  Credentialdetails

## Frontend

- Auf Desktop erscheint ein kompaktes Suchfeld in der App-Leiste.
- Auf kleinen Bildschirmen erscheint eine Suchschaltfläche, die einen ausreichend großen Dialog
  beziehungsweise ein mobiles Such-Overlay öffnet.
- `Ctrl+K` beziehungsweise `Cmd+K` fokussiert oder öffnet die Suche außerhalb der Setupseiten.
- Escape schließt die Ergebnisanzeige, ohne Navigation auszulösen.
- Ergebnisse sind vollständig mit Tastatur erreichbar.
- Pfeiltasten bewegen die aktive Auswahl; Enter öffnet das aktive Ergebnis.
- Die Oberfläche wartet nach Eingaben kurz, bevor eine Anfrage gesendet wird; der Richtwert beträgt
  250 Millisekunden.
- Veraltete Antworten schneller aufeinanderfolgender Suchen dürfen neuere Ergebnisse nicht
  überschreiben. Requests werden abgebrochen oder über eine eindeutige Anfragegeneration verworfen.
- Unter zwei Zeichen wird keine API-Anfrage gesendet.
- Ergebnisgruppen zeigen Kategorie, Treffer und verständliche Symbole.
- Jeder Treffer zeigt Titel und Kontext, ohne interne IDs als primäre Information darzustellen.
- Beim Auswählen wird über Vue Router auf den vom Backend gelieferten lokalen Pfad navigiert.
- Der Client akzeptiert nur relative, mit `/` beginnende docofhome-Pfade. Externe oder schemabehaftete
  URLs werden verworfen.
- Lade-, Mindestzeichen-, Leer-, Keine-Treffer- und Fehlerzustand sind optisch unterscheidbar.
- Dark Mode und Light Mode werden unterstützt.
- Suchfeld und Ergebnisdarstellung bleiben bei schmalen Mobilansichten ohne horizontales Scrollen
  bedienbar.
- Setup- und Backend-unavailable-Layout erhalten keine globale Suche.

## Migrationen

None.

Der Sprint fügt keine Tabelle, Spalte, Constraint oder persistierte Suchhistorie hinzu. Bestehende
UUIDs, Asset-Codes, Einstellungen, Beziehungen und Benutzerdaten bleiben unverändert.

## Tests

Backend unit/service/repository/API tests:

- Suche über jeden unterstützten Objekttyp
- Asset-Treffer über Code, Name, Produkt, Hersteller, Modell, Serien- und Inventarnummer
- Standorttreffer über Name und vollständigen Pfad
- Elektrotreffer über Bezeichnung, Assetdaten und Stromkreisnummer
- exakte Code- und Nummerntreffer vor Teiltreffern
- stabile Gruppierung und Sortierung
- Limit pro Typ und Gesamtzählung
- Soft-Delete-Verhalten und optionaler Archivparameter
- Escaping von `%`, `_`, Backslash, Anführungszeichen und Unicode
- zu kurze, zu lange oder fehlende Suchtexte
- ungültige Limits
- keine Ausgabe von Secrets oder Integrations-URLs

Direct database and constraint tests:

- None über bestehende Modul- und Foreign-Key-Abdeckung hinaus

Migration and update-safety tests:

- Bestätigung, dass der Alembic-Kopf unverändert bleibt
- bestehende Upgrade- und Fresh-Database-Prüfungen bleiben grün

Frontend/Vitest tests:

- keine Anfrage unter zwei Zeichen
- Debounce und Behandlung veralteter Antworten
- gruppierte Darstellung aller Typen
- Lade-, Leer-, Keine-Treffer- und Fehlerzustand
- Tastaturnavigation, Enter und Escape
- `Ctrl+K` und `Cmd+K`
- mobile Öffnung und Desktopfeld
- sichere Ablehnung externer oder ungültiger Routen
- Navigation zu jedem unterstützten lokalen Ziel

Regression and failure-path tests:

- App-Shell bleibt ohne Suchantwort nutzbar
- Integrationsausfall beeinflusst die lokale Suche nicht
- Setup- und unavailable-Layout bleiben unverändert
- bestehende Modulnavigation und Suchfelder funktionieren weiter

Required static, build, and Docker checks:

- Ruff
- mypy
- pytest
- Alembic Upgrade/Downgrade/Fresh-Database-Prüfungen gemäß Projektstandard
- Vitest
- vue-tsc
- Vite production build
- MDI-Iconprüfung
- Docker build

## Implementierungsstand

Im Paket `0.1.10-dev` umgesetzt:

- versionierter Endpunkt `GET /api/v1/search` mit fünf festen Ergebnisgruppen
- lokales Ranking, Feldkennzeichnung, Limits und sichere Archivroute für Assets
- Desktop-Suchfeld, mobiles Vollbild-Overlay und `Ctrl+K`/`Cmd+K`
- Debounce, Abbruch beziehungsweise Generationsschutz für veraltete Antworten
- Tastaturauswahl mit Pfeiltasten, Enter und Escape
- Backend- und Frontendtests für Kernverträge, Fehlerpfade und Routensicherheit
- keine Datenbankmigration; Alembic-Kopf bleibt `0016`

In der Erstellungsumgebung ausgeführt:

- Python-Syntaxprüfung aller Backend- und Testdateien
- Syntaxprüfung aller TypeScript- und Vue-Skripte sowie gezielte strikte Typprüfung der neuen
  Suchverträge, des API-Clients und des Such-Composables
- Prüfung der geänderten Vue-Templates, lokaler Markdownverweise, Versions- und
  Migrationskonsistenz, Whitespace, neuer Secrets und ZIP-Integrität

Noch in einer vollständigen Entwicklungs- oder Dockerumgebung auszuführen:

- Ruff, mypy und pytest mit den projektgebundenen Python-Abhängigkeiten
- Vitest, vue-tsc, MDI-Iconprüfung und Vite-Produktionsbuild mit `node_modules`
- Alembic-Upgrade-/Downgrade-/Fresh-Database-Prüfungen
- Docker-Build und manuelle Desktop-/Mobilabnahme

## Definition of Done

- [x] Jeder Anforderungspunkt dieses Sprints ist im Quellcode umgesetzt.
- [x] Es wurde kein Verhalten außerhalb des Sprintumfangs eingeführt.
- [x] Backend- und Frontendverträge sind typisiert und dokumentiert.
- [x] Die lokale Suche deckt alle fünf festgelegten Objekttypen ab.
- [ ] Ranking, Limits, Soft-Delete-Verhalten und Wildcard-Escaping sind getestet.
- [ ] Desktop-, Mobil- und Tastaturbedienung sind demonstriert.
- [x] Veraltete Antworten können aktuelle Ergebnisse nicht überschreiben.
- [x] Externe oder unsichere Navigationsziele werden nicht geöffnet.
- [x] Der Alembic-Kopf und sämtliche vorhandenen Daten bleiben unverändert.
- [ ] Ruff, mypy, pytest, Alembic, Vitest, vue-tsc, Vite und Docker sind grün.
- [x] README, CHANGELOG, ROADMAP, PROJECT_STATUS und dieser Sprintstatus wurden aktualisiert.
- [x] Das Paket enthält keine neuen Credentials, privaten URLs oder sachfremden Änderungen.
- [ ] Reviewfunde sind behoben und die Abnahmekriterien sind nachgewiesen.

## Abnahmekriterien

- Ein Benutzer kann einen bekannten Asset-Code in der App-Leiste eingeben und direkt zum Asset
  navigieren.
- Ein Raum wird sowohl über seinen Namen als auch über einen Bestandteil des vollständigen Pfads
  gefunden.
- Eine Verteilung, ein Schutzgerät und ein Stromkreis erscheinen jeweils in ihrer verständlichen
  Ergebnisgruppe.
- Eine exakte Stromkreisnummer beziehungsweise ein exakter Asset-Code steht vor unscharfen
  Teiltreffern.
- Die Suche funktioniert ohne konfigurierte Integrationen und bei nicht erreichbarem Home Assistant,
  Immich oder Nextcloud.
- Auf einem Mobilgerät kann die Suche ohne horizontales Scrollen vollständig bedient werden.
- Die komplette Suche ist per Tastatur nutzbar.

## Nicht Bestandteil

- Suche in Home Assistant, Immich oder Nextcloud
- Suche in noch nicht implementierten Dokumenten, Wiki-, Wartungs- oder Verbrauchsdaten
- Suchhistorie, Favoriten oder gespeicherte Suchabfragen
- Autovervollständigung mit externen Diensten
- semantische, KI-basierte oder Vektorsuche
- SQLite FTS, Elasticsearch, Meilisearch oder ein anderer zusätzlicher Suchdienst
- neue Detailseite für Schutzgeräte
- Änderungen, Löschungen oder Massenaktionen aus Suchergebnissen
- globale Archivsuche im ersten Frontendausbau
