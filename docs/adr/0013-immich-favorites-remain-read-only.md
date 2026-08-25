# ADR-0013 – Immich-Favoriten bleiben schreibgeschützt

## Status

Akzeptiert

## Kontext

Immich kennzeichnet Bilder mit `isFavorite`. Für die technische Hausdokumentation ist diese Markierung ein sinnvoller, bereits gepflegter Auswahlmechanismus. docofhome soll sie nutzen, ohne Eigentümerschaft oder Zustand der Bilder zu übernehmen.

## Entscheidung

docofhome darf den Favoritenstatus ausschließlich als serverseitigen Suchfilter und als sichtbare Metadaten verwenden. Die Anwendung bietet keine Aktion zum Setzen oder Entfernen eines Favoriten.

Der optionale API-Parameter `favorite_only=true` wird vom Backend in die Immich-Metadatensuche übersetzt. Der Browser kommuniziert weiterhin nur mit der same-origin docofhome-API.

## Folgen

- Die bestehende API-Key-Berechtigung bleibt auf lesende Asset-Rechte begrenzt.
- Es gibt keine Synchronisations- oder Konfliktlogik für Favoriten.
- Änderungen des Favoritenstatus erfolgen ausschließlich in Immich.
- Suche und Pagination bleiben korrekt, weil die Filterung nicht erst im Browser stattfindet.
