# ADR-0017: Ein Immich-Quellalbum und Asset-basierte Verteilungsbilder

## Status

Akzeptiert

## Entscheidung

docofhome speichert für die Immich-Integration höchstens eine Quellalbum-ID. Bildauswahldialoge
für Assets und elektrische Verteilungen verwenden diese ID serverseitig als Albumfilter und lassen
alle Ergebnisseiten erreichbar.

Eine elektrische Verteilung erhält keine eigene Fototabelle. Sie verwendet die bereits vorhandene
Asset-ID der Verteilung für Immich-Verknüpfungen. Dadurch gibt es genau eine Bildzuordnung und keine
widersprüchlichen Duplikate zwischen Asset- und Elektroansicht.

## Folgen

- Die Immich-Integration bleibt auf einen klaren, lesenden Auswahlworkflow begrenzt.
- Ein Wechsel des Quellalbums entfernt vorhandene Bildverknüpfungen nicht.
- Verknüpfte Metadaten bleiben lokal lesbar, auch wenn das Album später nicht erreichbar ist.
- Weitere Fotoziele benötigen eine eigene fachliche Entscheidung und werden nicht automatisch
  aus dieser Lösung abgeleitet.
