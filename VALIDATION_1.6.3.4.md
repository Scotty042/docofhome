# Validierung DocOfHome 1.6.3.4

## Behobener Laufzeitfehler

Die Kammschienen-Synchronisation verwendet nun `effective_asset_module_width` als Fallback,
wenn die historische Schutzgeräte-Spalte `module_width` leer ist. Das entspricht exakt der
Breitenanzeige der Verteilerschrankansicht.

## Abgesicherte Verträge

- Kandidatenermittlung akzeptiert geerbte DIN-Breiten
- TE-Überdeckung verwendet die wirksame statt nur der lokalen Breite
- Phasenberechnung verwendet dieselbe wirksame Breite
- serverseitige Fallback-Suche verwirft geerbte Breiten nicht mehr
- Regressionstest simuliert `electrical_protective_devices.module_width = NULL` bei
  `asset_types.module_width = 1`
- Synchronisationslauf schreibt Diagnosewerte in das Serverlog

## Ausgeführte Prüfungen

- Python-Syntaxprüfung
- Versions- und Releaseverträge
- dependency-freie Elektro- und Phasenschienenverträge
- TypeScript-/Vue-Syntaxprüfung
- ZIP- und Manifestprüfung

Die vollständige Pytest-Suite konnte in der Buildumgebung nicht ausgeführt werden, da das
Python-Paket `sqlmodel` nicht installiert und nicht aus dem Paketnetz abrufbar ist. Der
konkrete Regressionstest ist im Release enthalten und kann im Docker-Build ausgeführt werden.
