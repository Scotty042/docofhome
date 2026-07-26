# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.2.0

- DocOfHome besitzt keine Benutzerkonten oder Rollen und darf nur in einem
  vertrauenswürdigen privaten Netzwerk betrieben werden.
- Home-Assistant-Livewerte werden aus einem kurzlebigen Snapshot gelesen; es
  gibt keinen permanenten Eventstream und keine zusätzliche Langzeitspeicherung.
- Der erste HA-Abruf nach Start oder Cacheablauf muss die Zustände von Home
  Assistant einmal vollständig einlesen. Danach greifen Pagination und Cache.
- Allgemeine DIN-Geräte dokumentieren TE-Platzierung und HA-Werte, führen aber
  keine elektrische Lastfluss-, Selektivitäts- oder Normberechnung durch.
- Die optionale Online-Bildsuche nutzt Wikimedia Commons. Lizenzangaben werden
  angezeigt, müssen vor einer Veröffentlichung aber vom Betreiber geprüft werden.
- Bereits hochgeladene, später im Produktformular verworfene Bilder werden nicht
  automatisch als verwaiste Dateien bereinigt.
- Immich bleibt optional und read-only.
