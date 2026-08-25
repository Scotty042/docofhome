# Sprint 0005: Electrical distributions

- Status: Completed
- Target branch: `feature/electrical-distributions`
- Depends on: Sprint 0004, migration `0006`, ADR-0003, and ADR-0004

> Dieses Dokument ist der vollständige Implementierungsvertrag für Sprint 0005. Zusätzlich gelten
> die verbindlichen Regeln aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

JARVIS erhält die erste produktive Stufe des Elektro-Moduls. Benutzer können Haupt- und
Unterverteilungen sowie Sicherungen, FI/RCD, LS/MCB, FI/LS/RCBO und Überspannungsschutz vollständig
offline dokumentieren, hierarchisch ordnen, positionieren, bearbeiten und archivieren.

Elektrische Komponenten bleiben Rollen vorhandener Asset-Engine-Assets. Asset-UUID, unveränderlicher
JARVIS-Code und `Asset.location_id` bleiben die einzigen Identitäten für Inventar und Standort.
Dieser Sprint führt weder konkurrierende Assets noch eine zweite Location-Zuordnung ein.

## Hintergrund

Sprint 0004 stellt den typisierten Location-Baum bereit. Die Asset Engine besitzt stabile Assets,
Produkte, Locations, Archivierung und Ersatzhistorie. Sprint 0005 ergänzt ausschließlich
elektrische Rollen und deren fachspezifische Daten.

Sprint 0003 bleibt die langfristige Planung des gesamten Elektro-Moduls. Dieser Sprint setzt daraus
nur Verteilungen und Schutzgeräte um. Stromkreise, Kabel, Verbraucher, Medien, Integrationen,
Berechnungen und Steuerung bleiben ausdrücklich späteren Sprints vorbehalten.

## Anforderungen

### Identität und Rollen

- Unterstützte Rollen sind `distribution` und `protective_device`.
- Eine Rolle besitzt eine eigene stabile UUID und referenziert genau ein bestehendes Asset.
- Pro Asset darf höchstens eine aktive elektrische Rolle existieren.
- Das Asset muss aktiv, nicht ersetzt und einer aktiven Location zugeordnet sein.
- Archivierte oder ersetzte Assets erhalten keine neue Rolle.
- Archivierte Rollen und ihr verknüpftes Asset bleiben mit `include_deleted=true` lesbar.
- Eine elektrische Rolle kopiert weder Asset- noch Produkt- noch Location-Felder in die Datenbank.
- API-Read-Modelle dürfen Assetname, JARVIS-Code und berechneten Location-Pfad einbetten.

### Verteilungen

- Verteilungen verwenden `distribution_type` mit `main` oder `sub`.
- Eine Hauptverteilung besitzt keinen Parent; eine Unterverteilung besitzt genau einen aktiven
  Parent.
- Optionale Felder sind `designation`, `rows`, `modules_per_row`, `description` und `notes`.
- `rows` und `modules_per_row` bleiben unbekannt, wenn der Benutzer keinen Wert einträgt.
- Die Parent-Hierarchie ist azyklisch. Selbstzuordnung und Zuordnung unter einen eigenen Nachfolger
  werden abgelehnt.
- Verschieben ändert Parent und Typ in einer Transaktion: Parent `null` bedeutet Hauptverteilung,
  ein Parent bedeutet Unterverteilung.
- Verteilungen mit aktiven Unterverteilungen oder Schutzgeräten können nicht archiviert werden.
- Eine zweite aktive Verteilungsrolle für dasselbe Asset ist ausgeschlossen.

### Schutzgeräte

- Unterstützte `device_type`-Werte sind `fuse`, `rcd`, `mcb`, `rcbo` und `spd`.
- Jedes Schutzgerät gehört genau einer aktiven Verteilung.
- Das Schutzgeräte-Asset muss dieselbe aktive `location_id` wie das Verteilungs-Asset besitzen.
- Optionale Positionsfelder sind `row_number`, `start_position` und `module_width`.
- Eine bekannte Position ist nur vollständig, wenn alle drei Positionsfelder gesetzt sind.
- Teilweise Positionsdaten werden abgelehnt; vollständig unbekannte Positionen bleiben zulässig.
- Bekannte Modulintervalle derselben Reihe dürfen sich nicht überschneiden.
- Falls Reihen- oder Modulgrenzen der Verteilung bekannt sind, muss die Position innerhalb dieser
  Grenzen liegen.
- Technische Felder sind optional: `rated_current_a`, `residual_current_ma`, `characteristic`,
  `poles`, `breaking_capacity_ka`, `rcd_type`, `fuse_type` und `spd_type`.
- Zahlenwerte müssen positiv und konservativ begrenzt sein; es werden keine Standardwerte erzeugt.
- Ein Asset kann nicht gleichzeitig als aktives Schutzgerät in mehreren Verteilungen vorkommen.
- Archivierte Schutzgeräte bleiben historisch lesbar.

## Backend

Das Modul folgt Router -> Service -> Repository -> SQLModel/SQLite und wird unter
`app/{models,repositories,schemas,services}/electrical.py` gekapselt.

### Datenmodell

`electrical_components` ist die gemeinsame Rollenbasis:

- `id` UUID, Primärschlüssel
- `asset_id` UUID, Fremdschlüssel auf `assets.id`
- `role` mit `distribution` oder `protective_device`
- `created_at`, `updated_at`, `deleted_at`
- partieller Unique-Index auf `asset_id` für aktive Zeilen

`electrical_distributions` enthält genau eine Zeile je Verteilungsrolle:

- `id` UUID, Primär- und Fremdschlüssel auf `electrical_components.id`
- `parent_distribution_id` als optionaler Self-Foreign-Key
- `distribution_type` mit `main` oder `sub`
- optionale Bezeichnung, Reihen, Module pro Reihe, Beschreibung und Notizen
- Check-Constraints für Typ/Parent und positive plausible Kapazitäten

`electrical_protective_devices` enthält genau eine Zeile je Schutzgeräterolle:

- `id` UUID, Primär- und Fremdschlüssel auf `electrical_components.id`
- `distribution_id` als Fremdschlüssel auf `electrical_distributions.id`
- Typ, optionale vollständige Position, optionale technische Werte, Beschreibung und Notizen
- Check-Constraints für Gerätetyp, vollständige Positionsgruppe und positive plausible Werte

Die gemeinsame Basis stellt datenbankseitig sicher, dass ein Asset nur eine aktive elektrische Rolle
besitzt. Servicevalidierung stellt zusätzlich sicher, dass die spezialisierte Tabelle zur Rolle
passt und referenzierte Assets, Locations und Parent-Komponenten aktiv sind.

### Repository

- Repositories besitzen Joins auf Asset und Location, Suche, Filter, allow-listete Sortierung,
  stabile UUID-Tiebreaker, Pagination und historische Sichtbarkeit.
- Verteilungssuche umfasst Bezeichnung, Beschreibung, Assetname, JARVIS-Code und Location-Pfad.
- Schutzgerätesuche umfasst technische Freitextfelder, Assetname, JARVIS-Code und Location-Pfad.
- Der Tree-Endpunkt lädt alle passenden Verteilungen ohne versteckte 100er-Grenze.
- Asset-Kandidaten werden paginiert nach Assetname, JARVIS-Code oder vollständigem Location-Pfad
  gesucht und schließen aktive elektrische Rollen aus.

### Service und Transaktionen

- Services besitzen alle Referenz-, Hierarchie-, Standort-, Positions- und Archivierungsregeln.
- Erstellen, Bearbeiten, Verschieben und Archivieren sind transaktional und rollen bei jedem Fehler
  vollständig zurück.
- Fehlende Datensätze liefern 404, ungültige Referenzen oder technische Eingaben 422 und
  Hierarchie-, Rollen-, Standort-, Überlappungs- oder Archivkonflikte 409.
- Router enthalten ausschließlich HTTP-Mapping und Dependency Injection.

### API

Alle Endpunkte liegen unter `/api/v1/electrical`.

Verteilungen:

- `GET /distributions` mit Pagination, Suche, Sortierung, `distribution_type`, Parent,
  `location_id` und `include_deleted`
- `POST /distributions`
- `GET /distributions/tree`
- `GET /distributions/{id}` mit Zählwerten und allen aktiven direkten Schutzgeräten
- `PUT /distributions/{id}`
- `POST /distributions/{id}/move`
- `DELETE /distributions/{id}` für Soft Delete

Schutzgeräte:

- `GET /protective-devices` mit Pagination, Suche, Sortierung, `distribution_id`, `device_type`,
  `location_id` und `include_deleted`
- `POST /protective-devices`
- `GET /protective-devices/{id}`
- `PUT /protective-devices/{id}`
- `DELETE /protective-devices/{id}` für Soft Delete

Asset-Auswahl:

- `GET /available-assets` mit Rolle, Suche, Pagination und optionaler aktueller Rollen-ID
- Ergebnisse enthalten nur aktive, nicht ersetzte Assets mit aktiver Location und ohne andere
  aktive elektrische Rolle.

Keine paginierte Liste liefert mehr als 100 Einträge pro Seite. Vollständigkeit wird durch
Gesamtanzahl und Seitenzahl sichtbar; Tree- und eingebettete Detaillisten sind vollständig und
werden nicht still abgeschnitten.

## Frontend

- Der aktive Menüpunkt „Elektro“ führt zu `/electrical`.
- `/electrical` zeigt Suche, Filter und auf Desktop eine Verteilungshierarchie; mobil werden
  hierarchische Karten verwendet.
- `/electrical/distributions/new` und `/{id}/edit` bearbeiten Verteilungen.
- `/electrical/distributions/{id}` zeigt Breadcrumbs, Asset/Location, Kapazität,
  Unterverteilungs-/Gerätezahlen und Schutzgeräte nach Reihe und Position.
- Bekannte Positionen erscheinen in einer einfachen modularen Reihenansicht; Geräte ohne Position
  erscheinen getrennt unter „Position unbekannt“.
- Schutzgeräte werden unter `/electrical/protective-devices/new` und `/{id}/edit` bearbeitet.
- Asset-Auswahl ist serverseitig paginiert und durchsuchbar, lädt bei Bedarf alle Seiten und hat
  keine versteckte 100er-Grenze. Sie zeigt Name, JARVIS-Code und vollständigen Location-Pfad.
- Ein Link führt zur bestehenden Asset-Erstellung; es gibt keine zweite Asset-Erstellungslogik.
- Alle Listen besitzen sichtbare Pagination oder laden nachweislich die vollständige Tree-Liste.
- Lade-, Leer-, Validierungs-, Konflikt-, Archiv- und Backend-nicht-erreichbar-Zustände sind
  verständlich und responsive.
- Dark und Light Mode werden unterstützt.
- Detail- und Editorseiten beobachten Route-IDs, setzen veraltete Zustände zurück und ignorieren
  verspätete Antworten älterer Routen.

## Migrationen

Revision `0007` baut additiv auf `0006` auf und erstellt ausschließlich die drei elektrischen
Tabellen, Fremdschlüssel, Check-Constraints und Indizes. Es gibt keine Seed-Daten und keine
Änderung bestehender Assets, Locations, UUIDs, Einstellungen oder Beziehungen.

Die Migration wird auf leerer Datenbank und als Upgrade von `0006` mit vorhandenen Settings,
Locations, Assets und archivierten Daten getestet. `PRAGMA foreign_key_check` muss leer bleiben.
Der Downgrade entfernt nur elektrische Tabellen in abhängiger Reihenfolge und verändert keine
Asset- oder Location-Zeile.

## Tests

### Backend

- eindeutige aktive Rolle pro Asset sowie direkte Unique-/FK-Checks
- Ablehnung archivierter, ersetzter oder ortloser Assets und archivierter Locations
- Verteilung CRUD, Hierarchie, Self-/Nachfahrenzyklen, transaktionales Verschieben
- Archivschutz bei aktiven Unterverteilungen und Schutzgeräten
- Schutzgerätetypen, Standortgleichheit, doppelte Installation und archivierte Zielverteilung
- bekannte Position, Überlappung, Grenzen und erlaubte unbekannte Position
- positive/plausible technische Werte ohne Defaults
- Suche über Asset/Code/Location-Pfad, Filter, Sortierung und Pagination
- vollständiger Tree, Detailzahlen und historische Reads
- Migration frisch und von `0006`, Datenbewahrung, Downgrade-Sicherheit und Foreign Keys

### Frontend

- API-Verträge und Query-/Payload-Serialisierung
- mehr als 100 Asset-Kandidaten und mehr als 100 Schutzgeräte ohne stillen Verlust
- Verteilungshierarchie, Positionen, unbekannte Positionen und Archivkennzeichnung
- Formularnormalisierung und Validierungsfeedback
- Route A -> B sowie verspätete Antworten für Detail und Editor
- Routing und aktive Navigation

### Qualitätsprüfungen

- Ruff, mypy, pytest
- frisches `alembic upgrade head`, Upgrade von `0006`, `alembic check`
- Vitest, `vue-tsc --noEmit`, Vite Build
- Docker Build und vollständige GitHub Actions CI

## Definition of Done

- [x] Elektrische Rollen referenzieren ausschließlich bestehende Assets und Locations.
- [x] Verteilungen und alle fünf Schutzgerätetypen sind end-to-end nutzbar.
- [x] Hierarchie, Standortgleichheit, Position, Archivierung und Eindeutigkeit sind abgesichert.
- [x] CRUD, Tree, Move, Suche, Filter, Sortierung, Pagination und historische Reads sind verfügbar.
- [x] Responsive Desktop-/Mobilansichten funktionieren in Dark und Light Mode.
- [x] Keine Liste besitzt eine stille 100-Einträge-Begrenzung.
- [x] Migration `0007` ist additiv, update-sicher und bewahrt alle bestehenden Daten.
- [x] Backend-, Frontend-, Datenbank-, Migrations- und Lifecycle-Tests bestehen.
- [x] Ruff, mypy, pytest, Alembic, Vitest, vue-tsc, Vite, Docker und GitHub CI sind grün.
- [x] ADR, Architekturübersicht, README, CHANGELOG und Sprintstatus sind aktualisiert.
- [x] Der PR enthält keine privaten Werte, Zugangsdaten, generierten Daten oder TODO-Platzhalter.

## Prüfergebnis

- Backend: Ruff, mypy und 44 pytest-Tests erfolgreich.
- Migrationen: frisches Upgrade bis `0007`, `alembic check`, Upgrade von `0006`, Downgrade und
  Foreign-Key-Prüfung erfolgreich.
- Frontend: 39 Vitest-Tests, `vue-tsc --noEmit` und Vite-Produktionsbuild erfolgreich.
- Docker: Lokal nicht ausführbar, weil auf dem Entwicklungsrechner keine Docker-CLI installiert
  ist; der vollständige GitHub-Actions-Docker-Build in Draft-PR #5 ist erfolgreich.
- GitHub Actions: Backend, Frontend und Docker Build erfolgreich.

## Abnahmekriterien

1. Ein aktives, räumlich zugeordnetes Asset kann genau eine aktive elektrische Rolle erhalten.
2. Haupt- und Unterverteilungen bilden eine verschiebbare, azyklische Hierarchie.
3. Sicherung, FI/RCD, LS/MCB, FI/LS/RCBO und Überspannungsschutz sind mit optionalen technischen
   Daten dokumentierbar.
4. Bekannte Modulpositionen überlappen nicht; unbekannte Positionen bleiben zulässig und sichtbar.
5. Schutzgeräte und Verteilung besitzen über ihre Assets denselben aktiven Standort.
6. Archivschutz verhindert gebrochene aktive Hierarchien und Installationen; Historie bleibt lesbar.
7. Asset-Auswahl findet mehr als 100 geeignete Assets nach Name, JARVIS-Code oder Location-Pfad.
8. Listen und Schutzgerätedarstellung verlieren auch bei mehr als 100 Ergebnissen keine Daten.
9. Routenwechsel aktualisieren dieselbe Komponenteninstanz ohne veraltete oder verspätete Daten.
10. Upgrade von `0006` und Downgrade bewahren alle vorhandenen Asset-/Location-Daten und UUIDs.
11. Alle lokalen und GitHub-Actions-Prüfungen einschließlich Docker Build sind erfolgreich.

## Nicht Bestandteil

- Stromkreise und virtuelle Stromkreise; sie folgen in einem separaten Sprint.
- Kabel, Leitungsquerschnitte, Steckdosen, Lampen, Verbraucher und Gerätezuordnung zu Stromkreisen.
- Home Assistant, Live-Messwerte, Steuerung oder externe Integrationen.
- Schaltpläne, Fotos, Dokumente und Prüfprotokolle.
- Last-, Selektivitäts-, Spannungsfall-, Kurzschluss- oder Normberechnung.
- Automatische Elektroplanung, Prüfung, Zertifizierung oder Abnahme.
- Wiederherstellung oder physisches Löschen archivierter Daten.

JARVIS dokumentiert vom Benutzer eingetragene elektrische Daten. Es ersetzt keine Planung, Prüfung
oder Abnahme durch eine Elektrofachkraft.
