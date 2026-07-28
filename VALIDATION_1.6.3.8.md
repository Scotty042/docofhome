# DocOfHome 1.6.3.8 – Validierung

Stand: 28.07.2026

## Behobener Fehler

Das Auswahlfeld **Zugehöriger FI/RCD (optional)** an Phasen-/Kammschienen und
N-Schienen verwendete nur das historische Schutzgerätemodell. Ein als normales
DIN-Asset platzierter FI-Schutzschalter erschien deshalb nicht in der Liste.

## Umsetzung

- neue Datenbankreferenz `linked_rcd_asset_id` für Schrankkomponenten
- bestehende Referenz `linked_rcd_device_id` bleibt für Altbestände erhalten
- beide Referenzen schließen sich gegenseitig aus
- FI/RCD-DIN-Assets werden zentral anhand ihres Asset-Typs erkannt
- unterstützt werden insbesondere FI-Schutzschalter, FI/LS, RCD, RCBO und
  Fehlerstromschutzschalter
- auswählbar sind nur aktive und in derselben Verteilung platzierte DIN-Assets
- API-Antworten für DIN-Platzierungen enthalten `is_rcd`
- Schienendetails zeigen den Namen des ausgewählten FI/RCD-Assets
- ein verknüpftes FI/RCD-Asset kann nicht aus der Verteilung entfernt werden,
  solange die Zuordnung besteht

## Datenbank

- Alembic-Head: `0047`
- Migration: `0047_link_cabinet_rails_to_din_rcd_assets.py`
- Migrationstest auf SQLite: erfolgreich
- Fremdschlüssel, Index und Ausschluss der doppelten Referenz geprüft

## Ausgeführte Prüfungen

- Versionskonsistenz 1.6.3.8: erfolgreich
- Branding: erfolgreich
- Releasevertrag 1.6.3.8: erfolgreich
- Python-Syntax für App, Migrationen und Tests: erfolgreich
- TypeScript-/Vue-Syntax: 182 Einheiten erfolgreich
- Migrationsprüfungen 0030 bis 0047: erfolgreich
- reine Klassifikationsprüfung für FI/RCD-Asset-Typen: erfolgreich

## Nicht vollständig ausführbar

Der vollständige Pytest-, Ruff-, Mypy-, `vue-tsc`-, Vite- und Docker-Lauf konnte
in dieser Umgebung nicht ausgeführt werden, weil die externen Python-/npm-
Abhängigkeiten beziehungsweise Docker nicht installiert sind. Die dafür
vorgesehenen Tests und Releaseverträge sind im Paket enthalten.
