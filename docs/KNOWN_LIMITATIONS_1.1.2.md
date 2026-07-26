# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.1.2

- DocOfHome besitzt weiterhin keine Benutzerkonten oder Rollen und ist nur für
  ein vertrauenswürdiges privates Netzwerk vorgesehen.
- Home-Assistant-Livewerte werden beim Öffnen beziehungsweise manuellen
  Aktualisieren der Zählerübersicht gelesen. Es gibt in 1.1.2 noch keinen
  permanenten Websocket-Livestream und keine automatische Langzeitspeicherung
  dieser Momentanwerte.
- Pro Zähler werden eine Gesamtleistungs- und eine Spannungsentität angezeigt.
  Separate L1-/L2-/L3-Werte können weiterhin als normale HA-Entitäten
  dokumentiert werden, besitzen aber noch keine eigene Zählerdarstellung.
- Eine logische Netzwerkschnittstelle gruppiert Ports desselben Geräts. Bonding,
  STP, LACP, Routingtabellen und detaillierte VLAN-Taggingregeln werden nicht
  simuliert.
- Die Netzwerkprüfung bewertet die dokumentierte Gerätekonnektivität. Sie prüft
  weder reale Erreichbarkeit noch Linkstatus aus einem Switch-Management.
- Der Netzanschluss ist ein synthetischer externer Topologiepunkt aus der
  Energiekonfiguration. Ein optionales physisches HAK kann zusätzlich als Asset
  angelegt und dazwischen verbunden werden.
- Die Elektro-Topologie dokumentiert Verbindungen, prüft aber keine reale
  Lastflussrechnung, Selektivität oder normgerechte Auslegung.
- Die Immich-Großansicht verwendet die von der Integration bereitgestellte
  Vorschaudatei. Immich bleibt optional und read-only.
- Ein vollständiger Docker-Build und die dependency-basierten Testläufe müssen
  auf dem Zielsystem beziehungsweise in CI mit den im Lockfile festgelegten
  Paketen ausgeführt werden.
