# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.2.2

Die funktionalen Grenzen entsprechen 1.2.1 beziehungsweise 1.2.0:

- keine Benutzerkonten oder Rollen; Betrieb nur in einem vertrauenswürdigen
  privaten Netzwerk;
- HA-Livewerte stammen aus kurzlebigen Snapshots, nicht aus einem permanenten
  Eventstream;
- der erste HA-Abruf nach Start oder Cacheablauf muss die Zustände einmal
  vollständig einlesen;
- allgemeine DIN-Geräte führen keine Lastfluss-, Selektivitäts- oder
  Normberechnung durch;
- die optionale Wikimedia-Bildsuche erfordert eine eigenständige Lizenzprüfung
  durch den Betreiber;
- verworfene lokale Produktbilder werden nicht automatisch als verwaiste Dateien
  bereinigt;
- Immich bleibt optional und read-only.

Die vollständige abhängigkeitsbasierte Backend-, Frontend-, Docker- und reale
HA-Lastprüfung bleibt als Zielsystem-/CI-Abnahme offen. Der konkret gemeldete
MDI-Buildfehler ist mit 1.2.2 behoben. Details stehen in
`VALIDATION_REPORT_1.2.2.md`.
