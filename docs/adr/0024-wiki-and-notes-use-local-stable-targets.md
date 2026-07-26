# ADR-0024 – Wiki und Notizen verwenden lokale stabile Ziele

## Status

Accepted

## Entscheidung

Wiki-Seiten sind eigenständige lokale Datensätze mit UUID und hierarchischer Elternbeziehung.
Objektbezogene Notizen referenzieren ausschließlich allow-gelistete lokale Zieltypen und stabile
UUIDs. Es werden keine polymorphen freien Tabellennamen und keine externen Identifikatoren im
Browser akzeptiert.

## Folgen

- Notizen bleiben bei Umbenennungen des Zielobjekts stabil.
- Archivierte Ziele behalten ihre Historie schreibgeschützt.
- Die Anwendung validiert die Existenz jedes Ziels serverseitig.
