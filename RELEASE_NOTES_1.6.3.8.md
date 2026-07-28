# DocOfHome 1.6.3.8

## FI/RCD-Zuordnung für das aktuelle DIN-Geräte-Modell

Sicherungen, FI/RCD, FI/LS, Relais und weitere Einbaugeräte werden im aktuellen
Verteilerschrank als normale DIN-Assets platziert. Die optionale FI/RCD-Auswahl an
Phasen-/Kammschienen und N-Schienen berücksichtigte bisher jedoch nur das historische
`electrical_protective_devices`-Modell. Dadurch blieb die Auswahlliste leer, obwohl ein
FI-Schutzschalter sichtbar in derselben Verteilung platziert war.

Version 1.6.3.8 erweitert die Zuordnung auf beide Modelle:

- FI-Schutzschalter und FI/LS-Schalter aus den aktiven DIN-Asset-Platzierungen derselben
  Verteilung werden angeboten.
- Historische FI/RCD-Schutzgeräte bleiben weiterhin auswählbar.
- Eine Schiene speichert entweder den historischen Schutzgeräteverweis oder den neuen
  Asset-Verweis, niemals beide gleichzeitig.
- Der ausgewählte FI/RCD wird in den Schienendetails mit seinem Asset-Namen angezeigt.
- Ein als FI/RCD zugeordnetes DIN-Asset kann nicht aus dem Schrank entfernt werden, bevor
  die Schienenzuordnung gelöst wurde.
- Die Klassifikation erfolgt zentral anhand des Asset-Typs, unter anderem für
  `FI-Schutzschalter`, `FI/LS-Schalter`, RCD und RCBO.

## Datenbank

Alembic-Migration `0047` ergänzt `linked_rcd_asset_id` an den Schrankkomponenten. Der
bisherige Verweis `linked_rcd_device_id` bleibt für Altbestände vollständig erhalten.
