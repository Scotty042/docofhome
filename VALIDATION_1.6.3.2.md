# DocOfHome 1.6.3.2 – Validierungsbericht

Stand: 28. Juli 2026

## Anlass

In DocOfHome 1.6.3.1 konnte das Speichern einer Phasen-/Kammschiene weiterhin
„automatisch mit 0 Schutzgerät(en) verbunden“ melden, obwohl in der sichtbaren
Reihe vollständig überdeckte Sicherungen vorhanden waren.

## Technische Ursache

Die serverseitige Geräteermittlung konnte auf langfristig migrierten SQLite-
Datenbanken von der im Frontend sichtbaren Schutzgeräteliste abweichen. Außerdem
kann in älteren Datenbanken noch die historische Regel existieren, nach der ein
Ziel nur eine aktive Einspeisung besitzen darf. Dann muss eine vorhandene
manuelle Einspeisung deaktiviert werden, bevor der neue Kammschienenkontakt
aktiviert wird.

## Korrekturen

- Die Schrankansicht übermittelt beim Speichern alle aktuell sichtbaren
  Schutzgeräte-IDs der Verteilung.
- Das Backend prüft jede ID erneut auf aktive Existenz, Verteilung, Bereich,
  Reihe, vollständige TE-Überdeckung und berechenbare Phase.
- Die ID-Auflösung verwendet zuerst das kanonische Repository und fällt bei
  unvollständigen Projektionen direkt auf Basistabellen zurück.
- Die unabhängige serverseitige Verteilungssuche verbindet Repository und
  direkten lebenszyklusgeprüften Tabellen-Fallback.
- Neue automatische Kontakte werden zunächst inaktiv gespeichert.
- Vorhandene manuelle Einspeisungen und Messpunkte werden auf den neuen Kontakt
  umgehängt beziehungsweise archiviert.
- Erst danach wird der Kammschienenkontakt aktiv geschaltet.
- Bei vom Frontend gemeldeten Geräten ohne einen einzigen gültigen Kontakt wird
  der Speichervorgang mit einer verständlichen Fehlermeldung abgebrochen.
- Allgemeine DIN-Assets bleiben von der automatischen Verkabelung ausgenommen.

## Ausgeführte Prüfungen

- Versionskonsistenz 1.6.3.2
- Branding- und gesammelte Releaseverträge
- Elektro-Integritätsverträge 1.6.3
- expliziter Laufzeitvertrag für Kammschienen-Synchronisation
- echter SQLite-Laufzeittest mit:
  - L1/L2/L3-Ermittlung für TE 1/2/3;
  - historischer partieller Eindeutigkeitsregel für aktive Ziele;
  - inaktivem Vorabkontakt;
  - Umhängen eines Smart-Meter-Messpunkts;
  - Archivierung der alten Einspeisung;
  - anschließender Aktivierung des neuen Kontakts
- Python-Syntax aller Backend-, Migrations- und Testdateien
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten
- Migrationstests 0030 bis 0044
- ZIP-Kompressions-, Extraktions- und Manifestprüfung

## Nicht vollständig ausführbar

Die vollständige Pytest-Suite konnte in dieser Build-Umgebung nicht ausgeführt
werden, weil `sqlmodel` lokal nicht verfügbar war. `npm ci` konnte nicht komplett
aus dem lokalen Cache hergestellt werden, da das Paket `why-is-node-running`
fehlte. Der produktive Vue-/Vite-Build wurde daher hier nicht erneut vollständig
ausgeführt. Die geänderten Python-Dateien, Pydantic-Payloads und alle
TypeScript-/Vue-Skripteinheiten wurden syntaktisch geprüft.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0044`.
