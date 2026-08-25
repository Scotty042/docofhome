# Sprint 0014 – Immich-Galerievorschau

## Ziel

Die zentrale Immich-Galerie erhält eine zugängliche Detailvorschau, damit technische Fotos ohne Seitenwechsel größer betrachtet und innerhalb der aktuell geladenen Ergebnisse durchgesehen werden können.

## Umfang

- Klick- und tastaturbedienbare Bildkarten
- modaler Vorschaudialog mit Dateiname, Aufnahmezeit und Abmessungen
- sichtbare Kennzeichnung von Immich-Favoriten
- Vor-/Zurücknavigation ausschließlich innerhalb der aktuell geladenen Seite
- verständliche Fehlerdarstellung, wenn ein Vorschaubild nicht geladen werden kann
- mobile und Desktop-Darstellung
- keine Erweiterung der Immich-Schreibrechte

## Nicht enthalten

- Originaldatei-Download
- Vollbild-Originalauflösung
- Änderung des Favoritenstatus
- Upload, Löschen oder Bearbeiten in Immich
- Navigation über Seitengrenzen hinweg
- Album- oder Datumsfilter

## Architektur und Sicherheit

Die Vorschau verwendet weiterhin ausschließlich den bestehenden same-origin Thumbnail-Endpunkt von docofhome. API-Key und interne Immich-URL bleiben serverseitig. Die Navigation arbeitet nur mit bereits im Browser vorhandenen Metadaten und löst keine zusätzlichen Schreib- oder Originaldatei-Anfragen aus.

## Tests

- Formatierung bekannter und unbekannter Bildabmessungen
- Vor-/Zurücknavigation innerhalb einer geladenen Seite
- Grenzfälle am Anfang und Ende der Seite
- unbekannte aktuelle Bild-ID
- bestehende Frontend-, TypeScript-, Build-, Backend-, Migrations- und Docker-CI bleibt grün

## Definition of Done

- Bildkarten sind mit Maus und Tastatur bedienbar.
- Der Dialog zeigt das ausgewählte Vorschaubild und Metadaten.
- Navigation verlässt die aktuell geladene Seite nicht.
- Favoriten werden nur angezeigt, nicht verändert.
- Keine Zugangsdaten oder private Immich-Adressen gelangen in den Browser.
- CI ist vollständig erfolgreich.
