# ADR-0012: Immich-Vorschau verwendet ausschließlich Vorschaubilder

## Status

Angenommen

## Kontext

Die zentrale Bildergalerie benötigt eine größere Detailansicht. Immich kann neben Vorschaubildern auch Originaldateien ausliefern. Ein Originaldatei-Endpunkt würde jedoch deutlich größere Datenmengen, zusätzliche Medientypen und eine weitergehende Sicherheits- und Berechtigungsprüfung erfordern. Für die technische Hausdokumentation reicht zunächst eine vergrößerte Ansicht des bestehenden Vorschaubildes.

## Entscheidung

Die docofhome-Galerievorschau verwendet ausschließlich den bereits abgesicherten same-origin Thumbnail-Proxy.

- Es wird kein Originaldatei-Endpunkt ergänzt.
- Der Browser erhält weder Immich-API-Key noch interne Immich-URL.
- Favoritenstatus und Metadaten werden nur angezeigt.
- Vor- und Zurücknavigation bleibt auf die bereits geladene Ergebnisseite begrenzt.
- Ein fehlendes oder nicht ladbares Vorschaubild wird lokal und verständlich dargestellt.

## Folgen

### Positiv

- Die bestehende read-only Sicherheitsgrenze bleibt unverändert.
- Keine zusätzlichen Immich-Berechtigungen sind erforderlich.
- Datenvolumen und Speicherbedarf bleiben begrenzt.
- Die Vorschau funktioniert mit derselben Fehler- und Proxylogik wie die Galerie.

### Negativ

- Starkes Vergrößern kann sichtbare Qualitätsgrenzen des Vorschaubildes zeigen.
- Originalauflösung und Download stehen nicht zur Verfügung.
- Navigation über Seitengrenzen hinweg erfordert einen späteren, gesonderten Entwurf.

## Spätere Neubewertung

Ein Originaldatei-Workflow darf erst ergänzt werden, wenn Berechtigungen, Medientypbegrenzung, Größenlimits, Streaming, Downloadsemantik und mobile Datennutzung in einem eigenen Sprint verbindlich definiert und getestet sind.
