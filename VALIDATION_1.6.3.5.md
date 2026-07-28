# DocOfHome 1.6.3.5 – Validierung

Stand: 28.07.2026

## Anlass und bestätigte Ursache

Die reale Laufzeitanalyse zeigte, dass die im Verteilerschrank sichtbaren Geräte
nicht ausschließlich als `electrical_protective_devices`, sondern teilweise als
allgemeine `electrical_asset_placements` gespeichert sind. Die bisherige
Kammschienen-Synchronisation suchte überwiegend Schutzgeräte und konnte deshalb
trotz sichtbarer Sicherungen und Stromstoßschalter null Kontakte erzeugen.

## Umsetzung

- Jede vollständig von einer Phasen-/Kammschiene überdeckte DIN-Platzierung wird
  als physischer Kontakt behandelt.
- Schutzgeräte werden über den Endpunkt `protective_device`, allgemeine
  DIN-Platzierungen über den Endpunkt `asset` angebunden.
- Quelle der abgeleiteten Verbindung ist die Kammschiene; Ziel ist das jeweilige
  DIN-Gerät.
- Kontaktphasen folgen Startphase, TE-Position und belegter Breite.
- Ein vierpoliger FI/RCD oder FI/LS erhält L1, L2 und L3; der vierte Pol bleibt
  für N frei. Die zulässige Lage wird sowohl beim Platzieren des Geräts als auch
  beim späteren Anlegen der Schiene validiert.
- Zusätzliche manuelle Einspeisungen zu automatisch kontaktierten DIN-Geräten
  werden verhindert.
- Nachgelagerte Verbindungen allgemeiner DIN-Geräte übernehmen ebenfalls die
  wirksamen Schienenphasen.
- Anzeige, Kollisionsprüfung, Endpunktprojektion und automatische Verkabelung
  verwenden dieselbe wirksame DIN-Breite einschließlich Vererbung von Asset,
  Produkt oder Asset-Typ.
- Platzieren, Verschieben und Entfernen synchronisiert die Kontakte idempotent.
- Migration `0045` ergänzt die Kontakte für vorhandene DIN-Asset-Platzierungen
  und repariert bestehende Schienenbeziehungen.

## Erfolgreich ausgeführte Prüfungen

- Versions- und Brandingvertrag für `1.6.3.5`
- Releasevertrag und Elektro-Integritätsverträge
- Laufzeit-Quellvertrag für Schutzgeräte und allgemeine DIN-Assets
- Phasenmuster einschließlich vierpoligem FI-Sonderfall
- geerbte DIN-Breiten in Synchronisation und Platzierungsprüfung
- Syntax von 181 TypeScript-/Vue-Skripteinheiten
- Syntax von 280 Python-Dateien
- Migrationsprüfungen `0030` bis `0037` und `0039` bis `0045`
- Migration `0045` mit generischen DIN-Assets, L1/L2/L3-Folge,
  vierpoligem FI ohne N-Kontakt und wiederholtem idempotentem Upgrade
- ZIP-Kompressions-, Extraktions-, Manifest- und SHA-256-Prüfung

## Nicht vollständig ausführbare Prüfungen

- Die vollständige Pytest-Suite konnte in dieser Umgebung nicht ausgeführt
  werden, weil `sqlmodel` nicht installiert und nicht aus einem lokalen Cache
  verfügbar ist.
- `npm ci --offline` konnte nicht abgeschlossen werden, weil mindestens das
  Paket `why-is-node-running` nicht im npm-Cache vorhanden ist. Daher waren
  `vue-tsc`, Vitest und der vollständige Vite-Produktionsbuild hier nicht
  ausführbar.
- Docker ist in dieser Umgebung nicht installiert; ein Containerbuild konnte
  daher nicht lokal wiederholt werden.
- `ruff` ist nicht installiert. Stattdessen wurden Python-Syntax, Zeilenlängen
  und geänderte Importverwendungen separat geprüft.
