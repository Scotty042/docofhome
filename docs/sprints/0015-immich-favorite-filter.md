# Sprint 0015 – Immich-Favoritenfilter

## Ziel

Die zentrale Bildergalerie kann serverseitig auf in Immich markierte Favoriten eingeschränkt werden. Die Filterung muss mit Dateinamensuche und Pagination kombinierbar bleiben.

## Umfang

- optionaler API-Parameter `favorite_only`
- Weitergabe an die Immich-Metadatensuche als `isFavorite: true`
- responsiver Schalter „Nur Immich-Favoriten“ in der zentralen Galerie
- gemeinsames Zurücksetzen von Suche und Favoritenfilter
- unveränderte schreibgeschützte Integrationsgrenze

## Nicht im Umfang

- Favoritenstatus verändern
- Originaldateien oder Downloads
- Albumverwaltung
- lokale Kopien von Immich-Bildern

## Akzeptanzkriterien

- Ohne aktiven Filter bleibt das bisherige Ergebnis unverändert.
- Mit aktivem Filter liefert die API ausschließlich Immich-Favoriten.
- Suche, Favoritenfilter und Pagination werden serverseitig kombiniert.
- Der Browser erhält weiterhin weder API-Key noch interne Immich-URL.
- Backend-, Frontend- und Docker-CI sind grün.
