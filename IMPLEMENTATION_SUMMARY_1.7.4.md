# Implementierungsübersicht 1.7.4

## Frontend

- Neue Komponente `frontend/src/components/CabinetWiringOverlay.vue`.
- Dynamische SVG-Pfade anhand von `data-electrical-endpoint-key` und den
  aktiven Topologieverbindungen.
- Automatische Neuberechnung bei Größenänderung, Scrollen und aktualisierter
  Topologie.
- Reduzierung automatischer Kamm-/Sammelschienenkontakte.
- Externe Markierungen für Hausanschluss und ausgehende Verbindungen.
- Detaildrawer um ein- und ausgehende Verbindungen erweitert.
- Inline-Verkabelungszusammenfassungen aus der kompakten Schrankansicht
  entfernt.
- Phasen-Chips in Schrank-, Topologie- und Versorgungswegansichten vereinheitlicht.
- Reihenzähler auf Schutzgeräte, Assets und Schrankkomponenten erweitert.

## Backend und Datenbank

Für 1.7.4 waren keine Schema- oder API-Erweiterungen notwendig. Die vorhandene
Topologieantwort enthält alle benötigten Endpunkte und Verbindungen.
Alembic-Head bleibt `0049`.

## Tests

- Neuer statischer Vertrag für visuelle Verkabelung und externe Symbole.
- Ergänzte Verträge für Detailverbindungen und vollständige Reihenzähler.
- Releasevertrag prüft Version, Alembic-Head, Darstellungsmodi, Busbar-Reduktion,
  Kontrastklassen und die Abwesenheit der alten erweiterten Ansicht.
