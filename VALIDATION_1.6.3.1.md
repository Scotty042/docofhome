# DocOfHome 1.6.3.1 – Validierungsbericht

Stand: 28. Juli 2026

## Ausgangslage

Beim Speichern einer Phasen-/Kammschiene meldete DocOfHome trotz sichtbar und vollständig
überdeckter Sicherungen „automatisch mit 0 Schutzgeräten verbunden“. Die Schrankansicht und
die Automatiksynchronisation ermittelten aktive Schutzgeräte über zwei unterschiedliche
Datenpfade. Auf über mehrere Releases aktualisierten SQLite-Datenbanken konnten diese
Ergebnisse auseinanderlaufen.

## Korrektur

`PhaseRailConnectionService._devices_for_distribution()` verwendet jetzt
`ElectricalProtectiveDeviceRepository.for_distribution(..., include_deleted=False)`.
Dies ist derselbe kanonische Repositorypfad, über den die sichtbaren Schutzgeräte der
Verteilung bereitgestellt werden.

Damit gilt:

- jedes aktive Schutzgerät, das in der Verteilungsansicht sichtbar ist, steht auch der
  automatischen Kammschienen-Verkabelung zur Verfügung;
- vollständig überdeckte Schutzgeräte erhalten Quelle = Phasen-/Kammschiene und
  Ziel = Schutzgerät;
- allgemeine DIN-Assets bleiben von der automatischen Verkabelung ausgeschlossen;
- die vorhandene Verifikation bricht den Speichervorgang ab, falls erwartete Kontakte
  trotz erkannter Geräte fehlen oder eine falsche Phase besitzen;
- bestehende Schienen werden beim Speichern beziehungsweise beim Öffnen der Topologie
  erneut abgeglichen.

## Version und Datenbank

- Release: `1.6.3.1`
- Basis: `1.6.3`
- Alembic-Head: `0044`
- keine neue Migration erforderlich

## Erfolgreich ausgeführte Prüfungen

- zentrale Versionskonsistenz in `VERSION`, Backend, Frontend, Lockdatei und
  `SOURCE_INFO.json`;
- Branding- und gesammelte Korrekturverträge;
- Ableseerinnerungs-Verträge;
- Releasevertrag 1.6.3.1;
- Elektro-Integritätsverträge 1.6.3;
- neuer Laufzeitvertrag für den kanonischen Schutzgeräte-Repositorypfad;
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten;
- Python-Syntaxprüfung von Backend, Migrationen und Tests;
- dependency-freie Migrationsprüfungen 0030 bis 0044;
- ZIP-Kompressionsprüfung, erneute Extraktion und Manifestprüfung.

## Nicht ausführbare vollständige Gates

In der verfügbaren Umgebung fehlen `ruff`, `mypy`, `sqlmodel`/Pytest-Abhängigkeiten und
die installierten Frontend-Abhängigkeiten. Daher konnten die vollständigen Ruff-, mypy-,
Pytest-, Vitest-, vue-tsc-/Vite- und Docker-Läufe nicht erneut ausgeführt werden. Die
zugehörigen Quellen und Tests sind im Paket enthalten.
