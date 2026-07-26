# ADR-0005: Electrical roles for distributions and protective devices

- Status: Accepted
- Date: 2026-07-21

## Context

Das geplante Elektro-Modul benötigt Haupt- und Unterverteilungen sowie Schutzgeräte mit
fachspezifischen Hierarchie-, Standort- und Positionsregeln. Asset Engine und Spatial Model besitzen
bereits die stabilen Identitäten für Inventar und Standort. Separate Elektro-Assets oder eine zweite
Location-Zuordnung würden Daten duplizieren und könnten nach Umzug, Archivierung oder Ersatz eines
Assets widersprüchlich werden.

Technische Werte sind bei einer schrittweisen Bestandsaufnahme häufig noch unbekannt. Gleichzeitig
müssen bekannte Modulpositionen eindeutig sein, aktive Hierarchien intakt bleiben und bestehende
Installationen das additive Update ohne veränderte UUIDs oder Daten durchlaufen.

## Decision

- Elektrische Komponenten sind Rollen bestehender Assets. `electrical_components` speichert eine
  eigene Rollen-UUID, `asset_id`, den Rollenwert und Soft-Delete-Zeitstempel, aber keine kopierten
  Asset-, Produkt- oder Location-Felder.
- Ein partieller Unique-Index erlaubt je Asset höchstens eine aktive elektrische Rolle. Neue Rollen
  sind nur für aktive, nicht ersetzte Assets mit aktiver Location zulässig.
- `electrical_distributions` und `electrical_protective_devices` sind 1:1-Fachtabellen, deren
  Primärschlüssel zugleich Fremdschlüssel auf die gemeinsame Rollenbasis ist.
- Verteilungen verwenden `main` ohne Parent oder `sub` mit Parent. Parentwechsel ändern Typ und
  Parent transaktional. Zyklen, Selbstzuordnung sowie Archivierung mit aktiven Kindern oder Geräten
  werden in `ElectricalDistributionService` abgelehnt.
- Schutzgeräte unterstützen `fuse`, `rcd`, `mcb`, `rcbo` und `spd`. Ihr Asset muss dieselbe
  `Asset.location_id` wie das Verteilungs-Asset besitzen.
- Reihe, Startposition und Modulbreite sind gemeinsam bekannt oder vollständig unbekannt. Bekannte
  Intervalle dürfen sich innerhalb einer Reihe nicht überschneiden und müssen in bekannte
  Verteilungskapazitäten passen.
- Technische Daten bleiben nullable und erhalten keine vermuteten Standardwerte. Plausible positive
  Grenzen werden in Schema und Datenbank abgesichert.
- Router enthalten nur HTTP-Mapping und Dependency Injection. Services besitzen Regeln und
  Transaktionen; Repositories besitzen historische Sichtbarkeit, Projektionen, Suche, Filter,
  allow-listete Sortierung, Pagination und den vollständigen Baum.
- Die API liegt ausschließlich unter `/api/v1/electrical`. Paginierte Seiten sind auf 100 Einträge
  begrenzt und nennen Gesamtzahl sowie Seitenzahl. Tree und eingebettete Geräteliste werden
  vollständig und ohne stilles Limit geliefert.
- Die Vue-Oberfläche verwendet die vorhandenen Asset- und Location-Identitäten. Asset-Auswahlen
  lesen alle ausgewiesenen API-Seiten; Detail und Editoren ignorieren verspätete Antworten älterer
  Routen.
- Alembic-Revision `0007` erstellt nur die drei elektrischen Tabellen, Constraints und Indizes auf
  Basis von `0006`. Sie ändert und befüllt keine bestehende Zeile.

## Consequences

- Weitere Elektro-Sprints können Stromkreise, Kabel oder Dokumente an stabile Rollen-, Asset- und
  Location-UUIDs anbinden, ohne konkurrierende Inventaridentitäten einzuführen.
- Umzug oder Umbenennung eines Asset-Standorts erscheint sofort in Elektro-Reads, weil der
  Location-Pfad berechnet und nicht in der Elektrotabelle gespeichert wird.
- Ersetzte oder archivierte Assets erhalten keine neue Rolle. Ihre historischen Rollen bleiben mit
  expliziter historischer Sicht lesbar; ein physischer Ersatz übernimmt keine technischen Daten
  automatisch.
- Die Standortgleichheit schützt vor versehentlichen Installationen in einer fremden Verteilung,
  bedeutet aber, dass ein Verteilungs-Asset mit aktiven Geräten nicht allein an einen anderen Ort
  verschoben werden kann.
- Unbekannte Positionen und technische Werte sind zulässig und sichtbar. JARVIS dokumentiert
  Benutzereingaben, führt aber keine Planung, Normprüfung oder elektrische Berechnung durch.
- Wiederherstellung und physisches Löschen archivierter Rollen bleiben einem späteren
  Administrationsworkflow vorbehalten.
