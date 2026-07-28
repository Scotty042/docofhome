# DocOfHome 1.6.3.5

Diese Korrektur richtet die Kammschienenlogik am tatsächlichen Aufbau einer
DIN-Reihe aus. Eine Phasen-/Kammschiene kontaktiert nicht nur explizit als
Schutzgerät modellierte Einträge, sondern jedes vollständig überdeckte
DIN-Hutschienengerät.

## Behoben

- Als allgemeine DIN-Assets platzierte Sicherungen und Stromstoßschalter wurden
  bisher in der Schrankansicht angezeigt, aber von der automatischen
  Verkabelung nicht gefunden.
- Die Erfolgsmeldung konnte deshalb trotz sichtbarer Geräte `0` Kontakte melden.
- Teilweise unter einer Kammschiene liegende allgemeine DIN-Geräte waren möglich,
  obwohl deren Kontaktlage physisch nicht eindeutig ist.

## Neue Kontaktlogik

- Quelle jeder automatischen Verbindung ist die Phasen-/Kammschiene.
- Ziel ist entweder ein Schutzgerät oder das Asset einer allgemeinen
  DIN-Platzierung.
- Die Kontaktphase folgt Startphase und TE-Position.
- Mehrteilige allgemeine DIN-Geräte erhalten alle Phasen ihrer belegten Kontakte.
- Bei einem vierpoligen FI/RCD oder FI/LS werden ausschließlich L1, L2 und L3
  über die Schiene geführt; Pol 4 bleibt für N frei. Die zulässige Lage wird beim
  Platzieren des Geräts und beim späteren Anlegen der Schiene geprüft.
- Die Kontakte sind abgeleitet und können nicht manuell bearbeitet oder gelöscht
  werden. Zusätzliche manuelle Einspeisungen zu einem automatisch kontaktierten
  DIN-Gerät sind ebenfalls gesperrt.

## Datenbank

Migration `0045` ergänzt fehlende Schienenkontakte für vorhandene
DIN-Asset-Platzierungen und aktualisiert bestehende Kontakte idempotent.
