# Sprint 0007 – Hauptverteiler mit Feldern und Bereichen

## Ziel

Mehrspaltige Haupt- und Zählerverteiler werden realitätsnah abgebildet, ohne die einfache Reihenstruktur normaler Unterverteilungen unnötig zu verkomplizieren.

## Funktionsumfang

- Hauptverteilungen unterstützen optional den Aufbau `sections`.
- Unterverteilungen bleiben ausschließlich im Aufbau `rows`.
- Eine strukturierte Hauptverteilung enthält Felder, die in der Oberfläche nebeneinander dargestellt werden.
- Ein Feld enthält vertikal sortierte Bereiche.
- Unterstützte Bereichstypen:
  - Geräte- und Reihenbereich
  - Zählerfeld
  - Anschlussfeld
  - Technikbereich
  - Reserve
  - Abdeckung oder Blindfeld
- Nur Gerätebereiche dürfen Reihen und Module je Reihe definieren.
- Schutzgeräte können einem Gerätebereich und optional einer vollständigen Modulposition zugeordnet werden.
- Überlappung und Kapazität werden innerhalb des ausgewählten Bereichs geprüft.
- Technische Änderungen an einem Schutzgerät verändern dessen Feld-, Bereichs- oder Modulposition nicht.

## Bedienablauf

1. Hauptverteilung bearbeiten.
2. Aufbau `Felder und Bereiche` auswählen.
3. Felder wie `Links`, `Mitte` und `Rechts` anlegen.
4. Innerhalb jedes Feldes Bereiche von oben nach unten anlegen.
5. Schutzgeräte erfassen und anschließend in der Schrankaufteilung platzieren.
6. Technische Daten über den Schutzgeräte-Editor pflegen.

## Datenmigration

Migration `0008` ist additiv:

- Bestehende Verteilungen erhalten `layout_mode = rows`.
- Bestehende UUIDs, Asset-Codes, Hierarchien und Schutzgeräte bleiben erhalten.
- Neue Tabellen speichern Felder und Bereiche.
- Schutzgeräte erhalten optional `area_id`.

## Qualitätsanforderungen

- Ruff und striktes Mypy
- Backend- und Frontendtests
- Upgrade einer frischen Datenbank über die vollständige Alembic-Kette
- Produktionsbuild von Vue und Docker
- Keine versteckten Annahmen bei unbekannten Reihen- oder Modulwerten
- Keine globalen Positionskonflikte zwischen unterschiedlichen Feldern oder Bereichen
