# ADR-0014 – Immich-Datumsfilter bleiben serverseitig

## Status

Akzeptiert

## Kontext

Eine clientseitige Filterung der bereits geladenen Bilder würde bei paginierten Immich-Bibliotheken falsche Trefferzahlen und unvollständige Ergebnisse erzeugen. Immich stellt für die stabile Metadatensuche die Felder `takenAfter` und `takenBefore` bereit.

## Entscheidung

`docofhome` übergibt Aufnahmezeitraumfilter ausschließlich über das Backend an `POST /search/metadata`. Das Backend validiert die Reihenfolge des Zeitraums und kombiniert ihn mit den bestehenden Such-, Album- und Favoritenfiltern. Die Filter werden nicht persistiert.

Die Umsetzung bleibt vollständig schreibgeschützt. Es werden weder Immich-Daten noch lokale Fotoverknüpfungen verändert.

## Folgen

- Pagination und Trefferzahl bleiben korrekt.
- Immich bleibt die einzige Quelle für Aufnahmedaten und Suchergebnisse.
- Der Browser erhält weder API-Key noch interne Immich-URL.
- Eine spätere UI kann Datumsfelder oder vordefinierte Zeiträume anbieten, ohne den API-Vertrag erneut zu ändern.
