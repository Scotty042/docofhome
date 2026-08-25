# Sprint 0004: Spatial model

- Status: Completed
- Target branch: `feature/spatial-model`
- Depends on: Asset Engine, migration `0005`, and ADR-0003

> Dieses Dokument ist der vollständige Implementierungsvertrag für Sprint 0004. Zusätzlich gelten
> die verbindlichen Regeln aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

JARVIS erhält eine persistente, offline nutzbare Haus- und Raumstruktur als gemeinsame räumliche
Grundlage für Assets sowie spätere Module wie Elektro, Netzwerk, Dokumente, Wartung und Smart Home.

Version 1 verwaltet genau eine Installation beziehungsweise ein Haus. Die vorhandene Asset-Engine-
Entität `Location` wird additiv erweitert und bleibt die einzige Quelle für Standorte. Eine typische
Struktur kann Haus, Keller, Erdgeschoss, Obergeschoss, Garage, Werkstatt, Gartenhaus und
Außenbereich enthalten. Alle Bereiche können weitere Räume und Assets aufnehmen, ohne eigene
Elektroverteilungen vorauszusetzen.

## Hintergrund

Die Asset Engine besitzt bereits hierarchische Locations mit stabilen UUIDs und verbindet Assets
über `location_id`. Ein zweites Gebäude- oder Raummodell würde konkurrierende Identitäten und
unklare Zuständigkeiten erzeugen. Sprint 0004 erweitert deshalb dieselben Tabellen, APIs,
Repositories und Services.

Die Struktur muss sowohl auf neuen Installationen als auch auf Datenbanken mit vorhandenen
Locations funktionieren. Bestehende UUIDs, Namen, Beschreibungen, Hierarchien und Asset-Zuordnungen
bleiben erhalten. Die Migration ergänzt lediglich die Gebäudewurzel und fehlende Metadaten.

## Anforderungen

### Struktur und Typen

- Unterstützte Location-Typen sind `building`, `floor`, `room`, `area`, `cabinet`,
  `installation_point` und `outdoor`.
- Jede Location besitzt genau einen gültigen Typ.
- Pro JARVIS-Installation existiert genau eine aktive Root-Location.
- Die Root-Location hat den Typ `building` und keinen Parent.
- Jede andere Location besitzt einen aktiven Parent und darf nicht den Typ `building` haben.
- Garage, Werkstatt, Gartenhaus und Außenbereich werden je nach gewünschter Gliederung als `area`,
  `room` oder `outdoor` unter dem Haus angelegt; sie sind keine eigenen Gebäude.
- Es wird keine Mandanten-, Mehrhaus- oder komplexe Mehrgebäude-Architektur eingeführt.

### Hierarchie und Historie

- Location-UUIDs bleiben die relationalen Identitäten und werden niemals ersetzt.
- Die Hierarchie bleibt über `parent_id` in derselben `locations`-Tabelle gespeichert.
- Selbstreferenzen und direkte oder indirekte Zyklen sind verboten.
- Eine Location darf nicht unter sich selbst oder einen eigenen Nachfahren verschoben werden.
- Erstellen, Bearbeiten, Verschieben und Archivieren laufen jeweils in einer Transaktion.
- Archivierte Locations bleiben über historische Listen und Detailabfragen lesbar.
- Neue aktive Locations oder Assets dürfen keine archivierte Location referenzieren.
- Die Root-Location darf nicht archiviert werden.
- Eine Location mit aktiven direkten Kindern oder direkt zugeordneten aktiven Assets darf nicht
  archiviert werden.
- Archivierung ist Soft Delete über `deleted_at`; physisches Löschen ist nicht Bestandteil.

### Felder und berechnete Werte

`Location` enthält nach diesem Sprint:

- bestehende stabile `id`-UUID
- `name`
- verpflichtendes `location_type`
- `parent_id`
- `description`
- optionales `short_name`
- optionale `sort_order`
- optionale `notes`
- `created_at`
- `updated_at`
- `deleted_at`

Der vollständige Pfad, zum Beispiel `Haus / Erdgeschoss / Küche`, und die Breadcrumbs werden aus
der Hierarchie berechnet. Es wird keine redundante Pfadzeichenkette persistiert. Read-Modelle geben
zusätzlich die Anzahl direkt zugeordneter aktiver Assets und die Anzahl aktiver Assets in allen
Nachfahren zurück.

## Backend

Die bestehende Schichtung Router -> Service -> Repository -> SQLModel/SQLite bleibt erhalten.

### Modelle und Repository

- Das vorhandene SQLModel `Location` erhält die neuen Felder; es entsteht kein zweites
  Standortmodell.
- Ein Check-Constraint stellt die erlaubten Typwerte sowie die Root-/Parent-Grundregeln sicher.
- Ein partieller Unique-Index begrenzt aktive Root-Locations auf genau eine.
- `LocationRepository` besitzt Location-Abfragen, Hierarchie-Snapshots, Pfadberechnung,
  Breadcrumbs, Baumaufbau, Asset-Zählungen, Suche, Filterung, Sortierung und Pagination.
- SQLite-Fremdschlüssel bleiben auf jeder Anwendungsverbindung aktiv.

### Service und Domainregeln

- `LocationService` besitzt Validierung, Transaktionsgrenzen, Root-Regeln, Zyklusprüfung,
  Verschieben und Archivierung.
- Das Erstellen einer zweiten Root oder einer untergeordneten `building`-Location wird abgelehnt.
- Eltern müssen existieren und aktiv sein.
- Verschieben ändert nur `parent_id` und `updated_at`; bei einem Fehler bleibt die bisherige
  Hierarchie vollständig erhalten.
- Domainfehler werden als 404 für nicht vorhandene Ressourcen, 409 für Struktur- oder
  Archivierungskonflikte und 422 für ungültige Referenzen oder Eingaben ausgegeben.
- Router enthalten ausschließlich HTTP-Mapping und keine Geschäftslogik.
- `AssetService` lehnt neue oder geänderte Asset-Zuordnungen zu archivierten Locations weiterhin
  ab.

### API-Verträge

Alle Endpunkte bleiben unter `/api/v1`:

- `GET /locations` liefert paginierte Locations mit Suche nach Name oder vollständigem Pfad,
  Filter `location_type`, optionalem `parent_id`, Sortierung und `include_deleted`.
- `POST /locations` erstellt eine untergeordnete Location. Der bestehende Payload ohne
  `location_type` bleibt kompatibel und verwendet `area` als Standard, soweit die Root-Regeln dies
  erlauben.
- `GET /locations/tree` liefert die hierarchische Struktur in stabiler `sort_order`-/Name-Reihenfolge.
- `GET /locations/{id}` liefert Details, Pfad, Breadcrumbs und Asset-Zählungen.
- `PUT /locations/{id}` bearbeitet Stammdaten und kann den Parent transaktional ändern.
- `POST /locations/{id}/move` verschiebt ausschließlich den Parent transaktional.
- `DELETE /locations/{id}` archiviert die Location unter Einhaltung aller Schutzregeln.

Read-Modelle werden additiv um Typ, optionale Metadaten, `path`, `breadcrumbs`,
`direct_asset_count` und `descendant_asset_count` erweitert. Bestehende Felder und Endpunkte bleiben
erhalten.

### Ersteinrichtung

- Nach erfolgreichem Abschluss des First-Run-Wizards existiert eine aktive Gebäudewurzel.
- Root-Erstellung beziehungsweise initiale Benennung mit dem Installationsnamen erfolgt in
  derselben Transaktion wie der Setup-Abschluss.
- Ein Fehlschlag rollt Settings und Root-Änderungen gemeinsam zurück.
- Spätere Änderungen des Installationsnamens überschreiben einen vom Benutzer bearbeiteten
  Root-Namen nicht automatisch.

## Frontend

- Der Menüpunkt „Bereiche & Räume“ wird aktiviert und führt zu `/locations`.
- `/locations` bietet Suche, Typfilter und verständliche Lade-, Leer-, Fehler- und
  Nicht-erreichbar-Zustände.
- Desktop zeigt einen aufklappbaren Baum mit Typ, Pfad, Archivstatus und Asset-Zählungen.
- Mobil zeigt eine hierarchische Karten-/Listenansicht mit denselben Informationen.
- `/locations/new` und `/locations/{id}/edit` bieten responsive Formulare für Name, Typ, Parent,
  Beschreibung, Kurzname, Sortierreihenfolge und Notizen.
- `/locations/{id}` zeigt Breadcrumbs, Metadaten, direkte und untergeordnete Asset-Zählungen sowie
  die direkt zugeordneten Assets.
- Parent-Auswahl und Typauswahl verwenden nur gültige aktive Optionen; die Backend-Validierung
  bleibt autoritativ.
- Archivierte Einträge sind deutlich markiert und nicht als Ziel für neue Zuordnungen auswählbar.
- Dark und Light Mode werden unterstützt.
- Strukturänderungen erfolgen über Formularauswahl; Drag-and-Drop ist nicht vorhanden.
- Eine spätere Desktop-Layoutbearbeitung wird durch getrennte Baumkomponenten vorbereitet, aber
  weder sichtbar noch funktional implementiert.

## Migrationen

Eine neue additive Alembic-Revision `0006` baut auf `0005` auf:

1. `locations` erhält nullable `location_type`, `short_name`, `sort_order` und `notes`.
2. Alle bestehenden Locations werden deterministisch als `area` typisiert.
3. Eine neue Root-Location vom Typ `building` wird mit stabiler neuer UUID angelegt. Ihr Name stammt
   bei abgeschlossener Einrichtung aus `application_settings.installation_name`, sonst aus einem
   neutralen lokalen Standardwert.
4. Alle bisherigen Top-Level-Locations werden unter die neue Root gehängt. Ihre UUIDs, übrigen
   Felder, Unterhierarchien und Asset-Referenzen bleiben unverändert.
5. `location_type` wird verpflichtend; Check-Constraint und partieller Root-Unique-Index werden
   ergänzt.
6. `PRAGMA foreign_key_check` muss nach der Revision ohne Befund bleiben.

Die Revision funktioniert auf einer leeren Datenbank und beim Upgrade von `0005` mit bestehenden
Settings, Locations, Assets, archivierten Datensätzen und Hierarchien. Sie ändert keine vorhandene
Migration und speichert keine Pfadzeichenketten.

## Tests

- Backend-Service-/API-Tests für genau eine Root, CRUD, Root- und Parent-Regeln sowie klare
  Statuscodes.
- Tests für Selbstreferenzen, indirekte Zyklen, ungültige Hierarchien und transaktionales
  Verschieben einschließlich Rollback.
- Archivierungstests für Root, aktive Kinder und aktive Assets.
- Asset-Tests, die Zuordnungen zu archivierten Locations ablehnen und historische Reads erhalten.
- Pfad-, Breadcrumb-, Baum-, direkte/untergeordnete Asset-Zählungs-, Such-, Typfilter-, Sortier- und
  Paginationstests.
- Direkte SQLite-Tests für Fremdschlüssel, Typ-Check und Root-Unique-Index.
- Migrationsupgrade von `0005` mit bestehenden Settings, UUIDs, mehrstufigen Locations, Assets und
  archivierten Locations; kein Datenverlust und korrekte Root-Übernahme.
- Test für transaktionale Root-Erstellung beim First-Run-Setup und Persistenz nach Neustart.
- Frontend-Vitest-Tests für Routing, Query-/Payload-Verträge, Baumaufbereitung sowie mobile und
  Desktop-relevante Komponentenlogik.
- Ruff, mypy, pytest, frisches Alembic-Upgrade, Upgrade von `0005`, `alembic check`, Vitest,
  vue-tsc, Vite Build und Docker Build.

## Definition of Done

- [x] Die vorhandene Location-Entität ist additiv und ohne konkurrierendes Modell erweitert.
- [x] Genau eine Gebäudewurzel und alle Hierarchie-/Archivierungsregeln sind durch Service,
      Datenbank und Tests abgesichert.
- [x] Bestehende UUIDs, Daten, Hierarchien und Asset-Zuordnungen überstehen Migration `0006`.
- [x] Setup-Abschluss und Root-Erstellung sind transaktional.
- [x] CRUD, Baum, Pfade, Suche, Typfilter, Sortierung, Pagination und Verschieben sind unter
      `/api/v1/locations` verfügbar.
- [x] Responsive Listen-, Baum-, Detail- und Editorabläufe funktionieren auf Desktop und Mobil in
      Dark und Light Mode.
- [x] Archivierte Locations bleiben historisch lesbar und sind keine Ziele neuer Zuordnungen.
- [x] Alle beschriebenen Backend-, Frontend-, Datenbank- und Migrationstests bestehen.
- [x] Ruff, mypy, pytest, Alembic, Vitest, vue-tsc, Vite und Docker CI sind grün.
- [x] ADR, Architekturübersicht, README, CHANGELOG und Sprintstatus sind aktualisiert.
- [x] Der PR enthält keine Zugangsdaten, privaten URLs, generierten Daten oder sachfremden Änderungen.

## Abnahmekriterien

1. Eine neue Einrichtung legt mit dem Installationsnamen genau eine Gebäudewurzel an.
2. Ein Upgrade von `0005` bewahrt alle vorhandenen Location- und Asset-UUIDs und hängt bisherige
   Top-Level-Locations verlustfrei unter eine neue Root.
3. Benutzer können Keller, Etagen, Räume, Garage, Werkstatt, Gartenhaus und Außenbereiche mit
   passenden Typen hierarchisch dokumentieren.
4. Vollständige Pfade und Breadcrumbs spiegeln Erstellen, Bearbeiten und Verschieben unmittelbar
   wider, ohne gespeicherte Pfadspalte.
5. Selbstzuordnung, Nachfahrenzuordnung, zweite Root, Kind-Gebäude und archivierte Eltern werden mit
   verständlichen Fehlern abgelehnt.
6. Locations mit aktiven Kindern oder aktiven direkten Assets sowie die Root können nicht archiviert
   werden.
7. Detail- und Baumansicht zeigen direkte und untergeordnete aktive Asset-Anzahlen korrekt.
8. Suche findet sowohl Namen als auch Bestandteile vollständiger Pfade; Typfilter, Sortierung und
   Pagination liefern stabile Ergebnisse.
9. Desktop- und Mobilansicht unterstützen vollständige Navigation und Bearbeitung ohne Drag-and-Drop.
10. Alle lokalen und GitHub-Actions-Qualitätsprüfungen einschließlich Docker Build sind erfolgreich.

## Nicht Bestandteil

- Elektroverteilungen, Sicherungen, FI/RCD, LS, Stromkreise oder sonstige Elektroimplementierung.
- Grundrisszeichnung oder Desktop-Layouteditor.
- Drag-and-Drop für Hierarchieänderungen.
- GPS-Karten oder geografische Koordinaten.
- Immich-, Nextcloud- oder Home-Assistant-Anbindung.
- Dokumentenverwaltung.
- Mehrere Häuser, Gebäudeportfolios, Mandanten, Benutzerverwaltung oder Anmeldung.
- Physisches Löschen oder Wiederherstellung archivierter Locations.
