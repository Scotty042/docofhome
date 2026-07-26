# DocOfHome 1.1.2 – Release Notes

Veröffentlicht am 23. Juli 2026.

DocOfHome 1.1.2 bündelt die zehn nach 1.1.1 gemeldeten Korrekturen und
Erweiterungen. Das Release bleibt vollständig rückwärtskompatibel zu den
Verbrauchs-, Energie-, Elektro-, Asset-, Immich- und Netzwerkdaten aus 1.1.1.

## Zähler und Home Assistant

- Verbrauchszähler können mit einem vorhandenen Asset und einem Ort verknüpft
  werden. Fehlt ein eigener Ort, wird der Ort des zugeordneten Assets angezeigt.
- Pro Zähler können zusätzlich zur kumulativen Ablese-Entität je eine
  Home-Assistant-Entität für aktuelle Gesamtleistung und Spannung gewählt
  werden.
- Die Zählerübersicht zeigt verfügbare Livewerte in Watt und Volt. Initiale
  Abfragen teilen sich den lokalen HA-Snapshot; die Aktualisieren-Schaltfläche
  erzwingt einen frischen Abruf. Ein Ausfall von Home Assistant verhindert weder
  manuelle Ablesungen noch die restliche Zählerverwaltung.
- Verbrauchszähler können in Zählerfeldern eines Zählerschranks platziert,
  verschoben und wieder entfernt werden.
- Noch nicht mit einem Verbrauchszähler verknüpfte Assets vom Typ **Zähler**
  können ebenfalls direkt platziert werden. Eine spätere Doppelplatzierung
  desselben physischen Zählers wird verhindert.

## Assets, Immich und Orte

- Verknüpfte Immich-Bilder in der Asset-Ansicht öffnen sich per Klick oder
  Tastatur in einer großen Vorschau.
- Ortsauswahlen werden hierarchisch nach Gebäude, Etage und den jeweiligen
  Räumen sortiert. Hinterlegte `sort_order`-Werte haben Vorrang; innerhalb
  derselben Ebene wird deutsch-alphabetisch sortiert.

## Zählerschrank und Elektro-Topologie

- Neue Bereichstypen **N-Schiene** und **PE-Schiene** stehen zur Verfügung.
- Bereiche können volle oder halbe Breite besitzen. Zwei aufeinanderfolgende
  halbe Bereiche werden im Schrankplan nebeneinander dargestellt.
- Beim Anlegen und Bearbeiten einer elektrischen Verteilung sind ausschließlich
  Assets vom Typ **Elektrische Verteilung** zulässig. Diese Regel wird sowohl
  in der Auswahl als auch serverseitig erzwungen.
- Der in der Energiekonfiguration gepflegte Netzanschluss erscheint als echter
  externer Quellpunkt der Elektro-Topologie und kann beispielsweise mit HAK,
  Hauptsicherung, SLS, Zähler oder Verteilung verbunden werden. Als Ziel ist er
  bewusst nicht zulässig.

## Netzwerk

- Physische Ports können einer virtuellen beziehungsweise logischen
  Schnittstelle wie `LAN-Bridge`, `Management` oder einem VLAN zugeordnet
  werden. Eine Bridge mit Mitgliedsports bleibt vor einem versehentlichen
  Wechsel zu einem physischen Porttyp geschützt.
- IP-Adressen liegen auf der logischen Schnittstelle; eine primäre Adresse wird
  direkt am Gerät angezeigt. Dadurch lassen sich Router, Repeater und Geräte
  mit mehreren LAN-Ports fachlich korrekt abbilden.
- Die bestätigte FRITZ!Box-Übernahme legt für Geräte mit IP eine logische
  Management-/LAN-Schnittstelle an und ordnet den erkannten physischen oder
  drahtlosen Anschluss dieser zu.
- Freie Switch-Ports werden neutral als **Frei** angezeigt. Eine Warnung
  entsteht nur, wenn ein netzwerkfähiges Gerät insgesamt keine aktive
  Verbindung und keinen WLAN-/Mobilfunk-Uplink besitzt.

## Datenbank und Kompatibilität

- Neue Alembic-Revision: `0028_collected_integration_fixes`.
- Die Migration ergänzt nur neue Spalten, Constraints und die Tabelle für
  Zählerplatzierungen. Bestehende Daten bleiben erhalten.
- Der geprüfte Migrationspfad umfasst `0027 -> 0028`, `0028 -> 0027` und ein
  erneutes Upgrade auf `0028`.
