# ADR-0016: Immich-Alben bleiben schreibgeschützt

## Status

Angenommen.

## Kontext

Immich-Alben eignen sich zur vorhandenen fachlichen Gruppierung technischer Fotos. docofhome benötigt diese Gruppierung für die Suche und Anzeige, soll aber weder Eigentümer der Alben werden noch deren Freigaben oder Inhalte verändern.

## Entscheidung

- docofhome liest Alben ausschließlich serverseitig über `GET /albums`.
- Der Immich-API-Key benötigt für diese optionale Funktion zusätzlich `album.read`.
- In der lokalen Datenbank werden weder Albumkopien noch Synchronisationszustände gespeichert.
- Die ausgewählte Album-ID ist ein flüchtiger Ansichtsparameter und wird nur an die bestehende serverseitige Metadatensuche weitergereicht.
- Fehlt `album.read`, bleibt die normale Bildergalerie funktionsfähig; nur die Album-Auswahl zeigt einen verständlichen Hinweis.
- Schreibende Albumoperationen sind ausdrücklich nicht Teil des Connectors.

## Folgen

### Positiv

- Immich bleibt alleinige Quelle und Eigentümerin der Albumstruktur.
- Keine veralteten lokalen Albumkopien oder Konfliktauflösung sind nötig.
- API-Key und private Immich-Adresse bleiben außerhalb des Browsers.
- Album-, Favoriten-, Datums- und Dateinamensuche bleiben serverseitig kombinierbar.

### Einschränkungen

- Die Albumübersicht funktioniert nur mit der zusätzlichen Berechtigung `album.read`.
- Offline steht keine Albumliste zur Verfügung.
- Albumverwaltung und automatische Zuordnung bleiben bewusst ausgeschlossen.
