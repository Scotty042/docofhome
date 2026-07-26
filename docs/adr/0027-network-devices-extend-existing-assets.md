# ADR-0027 – Netzwerkgeräte erweitern bestehende Assets

## Status

Accepted

## Kontext

Router, Switches, Access Points, NAS-Systeme und Server sind bereits reale Geräte im Asset-Modul.
Ein zweites, unabhängiges Netzwerkgeräteverzeichnis würde Namen, Räume, Produkte, Bilder,
Dokumente und Lebenszyklen duplizieren und später widersprüchliche Identitäten erzeugen.

## Entscheidung

Ein Netzwerkgerät ist eine optionale technische Rolle eines bestehenden Assets. Die Tabelle
`network_devices` referenziert genau ein Asset und speichert ausschließlich netzwerkspezifische
Daten. Schnittstellen, IP-Adressen und Verbindungen hängen an dieser Rolle. Eine aktive
Netzwerkrolle muss vor Archivierung oder Ersatz des Assets archiviert werden.

IP-Netze und VLANs sind eigenständige lokale Fachdaten, weil sie nicht einem einzelnen Asset
gehören. Die Topologie wird ausschließlich aus ausdrücklich dokumentierten Verbindungen abgeleitet.

## Folgen

- Name, Raum, Produkt, Bilder, Notizen und Dokumente besitzen eine einzige führende Identität.
- Netzwerkgeräte erscheinen automatisch im normalen Asset-Lebenszyklus.
- Eine Netzwerkrolle kann entfernt und später neu angelegt werden, ohne das Asset zu löschen.
- Automatische Discovery bleibt ein späterer, klar abgegrenzter Importprozess und darf die lokale
  Dokumentation nicht ungefragt überschreiben.
