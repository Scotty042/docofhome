# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.1.3

- DocOfHome besitzt weiterhin keine Benutzerkonten oder Rollen und ist nur für
  ein vertrauenswürdiges privates Netzwerk vorgesehen.
- Home-Assistant-Livewerte werden beim Öffnen beziehungsweise manuellen
  Aktualisieren der Zählerübersicht gelesen. Es gibt noch keinen permanenten
  Websocket-Livestream und keine automatische Langzeitspeicherung dieser
  Momentanwerte.
- Pro Zähler werden eine Gesamtleistungs- und eine Spannungsentität angezeigt.
  Separate L1-/L2-/L3-Werte besitzen noch keine eigene Zählerdarstellung.
- Eine logische Netzwerkschnittstelle gruppiert Ports desselben Geräts. Bonding,
  STP, LACP, Routingtabellen und detaillierte VLAN-Taggingregeln werden nicht
  simuliert.
- Die Netzwerkprüfung bewertet die dokumentierte Gerätekonnektivität. Sie prüft
  weder reale Erreichbarkeit noch Linkstatus aus einem Switch-Management.
- Die Elektro-Topologie dokumentiert Verbindungen, prüft aber keine reale
  Lastflussrechnung, Selektivität oder normgerechte Auslegung.
- Immich bleibt optional und read-only.
