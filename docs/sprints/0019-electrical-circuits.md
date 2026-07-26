# Sprint 0019: Stromkreisdokumentation

- Status: Implemented locally; Docker validation pending
- Target branch: `feature/electrical-circuits`
- Depends on: Sprint 0005, Sprint 0007, Sprint 0008

> Dieses Dokument ist der vollständige Implementierungsvertrag für diesen Sprint. Zusätzlich gelten
> die verbindlichen Regeln aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

docofhome dokumentiert Stromkreise innerhalb einer elektrischen Verteilung. Ein Stromkreis besitzt
eine frei vergebene Bezeichnung, optional eine Nummer sowie Beschreibung und Notizen. Er kann
optional genau einem vorhandenen Schutzgerät derselben Verteilung zugeordnet werden.

## Hintergrund

Verteilungen und Schutzgeräte sind bereits update-sicher und Asset-basiert vorhanden. Für eine
vollständige Hausdokumentation fehlt die fachliche Ebene der von diesen Geräten versorgten
Stromkreise. Stromkreise sind eigenständige Dokumentationsdatensätze und keine Assets, weil sie kein
physisches Gerät mit Inventaridentität darstellen.

Die Immich-Integration bleibt auf das Durchsuchen von Alben und die manuelle Fotoauswahl für Assets
begrenzt. Dieser Sprint erweitert weder Immich noch Fotoverknüpfungen.

## Anforderungen

- Stromkreise können innerhalb einer aktiven Verteilung erstellt, gelesen, bearbeitet, gesucht,
  gefiltert, sortiert und archiviert werden.
- Name ist verpflichtend; Nummer, Schutzgerät, Beschreibung und Notizen sind optional.
- Eine nichtleere Stromkreisnummer ist innerhalb einer aktiven Verteilung eindeutig.
- Ein ausgewähltes Schutzgerät muss aktiv sein und zur selben Verteilung gehören.
- Beim Archivieren bleiben Stromkreis-ID, Daten und historische Schutzgerätezuordnung erhalten.
- Verteilungen und Schutzgeräte mit aktiven Stromkreisen können nicht archiviert werden.
- Es werden keine elektrischen Kennwerte, Phasen, Verbraucher oder Raumzuordnungen angenommen.
- Die Funktion arbeitet vollständig lokal und benötigt keine externe Integration.

## Backend

- Neue Tabelle `electrical_circuits` mit stabiler UUID, `distribution_id`, optionaler
  `protective_device_id`, Name, optionaler Nummer, Beschreibung, Notizen sowie Zeitstempeln und
  `deleted_at`.
- Endpunkte unter `/api/v1/electrical/circuits` für paginierte Liste, Detail, Erstellen, Bearbeiten
  und Soft Delete.
- Listenparameter: Pagination, Suche, allow-list Sortierung, `distribution_id`,
  `protective_device_id` und `include_deleted`.
- Repository besitzt Abfragen, Filter, Sortierung und Sichtbarkeit. Service besitzt Referenzprüfung,
  Eindeutigkeitsregeln und Transaktionsgrenzen. Router übersetzt bekannte Domänenfehler.
- API-Antworten enthalten lesbare Verteilungs- und optionale Schutzgerätebezeichnungen, ohne die
  bestehende Verteilungs-API zu brechen.

## Frontend

- Die Verteilungsdetailseite zeigt einen responsiven Bereich `Stromkreise` mit Lade-, Leer-, Fehler-
  und Erfolgszuständen.
- Aktive Verteilungen bieten `Stromkreis hinzufügen`, Bearbeiten und Archivieren.
- Ein gemeinsamer Editor unterstützt Erstellen und Bearbeiten, lädt die gewählte Verteilung und
  bietet nur deren aktive Schutzgeräte an.
- Formulare funktionieren in Dark und Light Mode sowie auf Mobilgeräten und Desktop.

## Migrationen

- Neue additive Revision `0013` nach `0012`.
- Fremdschlüssel auf Verteilung und optionales Schutzgerät.
- Indizes für Verteilung, Schutzgerät und Archivstatus.
- Partieller eindeutiger Index für nichtleere aktive Stromkreisnummern je Verteilung.
- Keine vorhandenen Tabellen, UUIDs oder Daten werden geändert oder zurückgesetzt.

## Tests

- Backend-API-Tests für CRUD, Suche, Filter, Pagination und Soft Delete.
- Validierungstests für falsche Verteilung, fremdes/archiviertes Schutzgerät und doppelte Nummer.
- Archivschutz für Verteilungen und Schutzgeräte mit aktiven Stromkreisen.
- Direkte Datenbanktests für Fremdschlüssel und partiellen Eindeutigkeitsindex.
- Migrationstest für frische Datenbank, Upgrade von `0012` und Downgrade.
- Frontendtests für API-Verträge, Editor-Hilfsfunktionen und Routen.
- Ruff, Mypy, Pytest, Alembic Upgrade/Check, Vitest, vue-tsc, Vite und soweit lokal verfügbar Docker.

## Definition of Done

- [x] Jeder Umfang dieses Sprints ist implementiert.
- [x] Kein Verhalten außerhalb des Sprints wurde ergänzt.
- [x] Backend- und Frontendverträge sind typisiert und dokumentiert.
- [x] Migration `0013` ist additiv und update-sicher.
- [x] Tests decken Erfolg, Validierung, Fehler und historische Lesbarkeit ab.
- [x] Ruff, Mypy, Pytest, Alembic, Vitest, vue-tsc und Vite sind grün.
- [ ] Docker-Build ist in einer Umgebung mit Docker Engine bestätigt.
- [x] README, CHANGELOG und dieser Sprint sind aktualisiert.
- [x] Keine Zugangsdaten, privaten URLs oder generierten Daten sind enthalten.

## Nicht Bestandteil

- Ausbau der Immich-Integration, Favoriten- oder Zeitfilter und neue Fotoverknüpfungen.
- Verknüpfungen von Bildern mit Räumen, Verteilungen oder Stromkreisen.
- Automatische Erkennung oder Erzeugung von Stromkreisen aus Schutzgeräten.
- Phasen-, Kabel-, Ader-, Messwert-, Last-, Verbraucher- oder Stromlaufplanmodellierung.
- Drag-and-drop, Sammelimport, Export oder automatische Nummerierung.
- Änderung bestehender technischer Legacy-Bezeichner.
