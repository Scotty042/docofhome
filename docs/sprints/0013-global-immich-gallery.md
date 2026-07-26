# Sprint 0013 – Zentrale Immich-Bildergalerie

Status: Implementiert, Live-Abnahme ausstehend

## Ziel

Das Pflichtenheft sieht Bilder als eigenständigen, zentral erreichbaren Bestandteil von docofhome vor. Nach den Asset-bezogenen Immich-Verknüpfungen aus Sprint 0011 wird deshalb eine globale, schreibgeschützte Bilderansicht ergänzt.

## Umfang

- eigener Navigationspunkt `Bilder`
- neue Route `/images`
- responsive Galerie mit 36 Bildern pro Seite
- serverseitige Suche nach Dateiname
- vollständige Pagination ohne stille Ergebnisbegrenzung
- Anzeige von Aufnahmedatum und Bildabmessungen
- verständliche Zustände für Laden, leere Ergebnisse und Integrationsfehler
- ausschließliche Nutzung des bestehenden serverseitigen Thumbnail-Proxys

## Sicherheitsgrenze

- kein Immich-API-Key im Browser
- keine interne Immich-URL im Browser
- keine Uploads, Änderungen, Löschungen, Albumaktionen oder Originaldownloads
- keine lokale Duplizierung der Bilddateien
- Fehlertexte enthalten keine externen Antwortkörper oder Zugangsdaten

## Kompatibilität

Der Sprint ändert weder Datenmodell noch Alembic-Historie. Bestehende Asset-Verknüpfungen und technische Legacy-Bezeichner bleiben unverändert.

## Abnahme

- Navigation öffnet `/images`
- Galerie lädt über die bestehende docofhome-API
- Suche und Pagination funktionieren mit großen Immich-Bibliotheken
- mobile und Desktop-Darstellung bleiben bedienbar
- deaktiviertes oder nicht erreichbares Immich erzeugt einen verständlichen Warnzustand
- Frontend-CI und Produktionsbuild sind grün

## Bewusste Folgearbeiten

- Filter nach Album, Datum und Favoriten
- Verknüpfung eines Bildes mit Räumen, Verteilungen und weiteren Domänenobjekten
- explizite Auswahl eines Titelbildes
- eigener Bilddetaildialog
