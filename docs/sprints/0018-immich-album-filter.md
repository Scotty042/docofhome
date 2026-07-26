# Sprint 0018 – Immich-Albumübersicht und Albumfilter

## Status

Implementiert auf `feature/immich-album-filter`.

## Ziel

Die zentrale Bildergalerie kann die für den angemeldeten Immich-Benutzer erreichbaren Alben schreibgeschützt anzeigen und Bilder serverseitig auf ein ausgewähltes Album begrenzen. Trefferzahl und Pagination bleiben dadurch auch bei großen Bibliotheken korrekt.

## Umfang

- neuer lokaler Endpunkt `GET /api/v1/immich/albums`
- serverseitiger Abruf über den stabilen Immich-Endpunkt `GET /albums`
- alphabetisch sortierte Albumliste mit Name, Medienanzahl, Zeitraum und optionalem Vorschaubild
- Album-Auswahl in der zentralen Bildergalerie
- Kombination mit Dateinamensuche, Favoritenfilter, Aufnahmezeitraum und Pagination
- verständlicher Teilfehler, wenn dem API-Key die Berechtigung `album.read` fehlt
- keine Datenbankmigration und keine lokale Kopie von Alben oder Bildern

## Sicherheitsgrenze

- ausschließlich lesende Immich-Aufrufe
- benötigte Immich-Berechtigungen: weiterhin `asset.read` und `asset.view`, zusätzlich `album.read`
- kein API-Key und keine interne Immich-URL im Browser
- keine Albumanlage, Freigabe, Umbenennung, Löschung oder Änderung von Albuminhalten
- keine Uploads, Originaldownloads oder Änderungen an Bildern
- Vorschaubilder laufen weiterhin ausschließlich über den begrenzten docofhome-Proxy

## Abnahme

- Alben werden alphabetisch und mit Medienanzahl angezeigt
- die Auswahl eines Albums setzt `album_id` bei der lokalen Bilderabfrage
- alle vorhandenen Galeriefilter bleiben kombinierbar
- eine fehlende Album-Berechtigung verhindert nicht die normale Bildergalerie
- Backend-, Frontend-, Migrations- und Docker-CI sind grün
