# DocOfHome 1.1.3 – Release Notes

Veröffentlicht am 23. Juli 2026.

DocOfHome 1.1.3 ist ein Build-Korrekturrelease für 1.1.2. Es enthält den
vollständigen Funktionsumfang von 1.1.2 unverändert und behebt den Abbruch des
Frontend-Builds bei der MDI-Icon-Prüfung.

## Korrigiert

- Das nicht in `@mdi/font` 7.4.47 vorhandene Icon `mdi-ground-wire` wurde bei
  der PE-Schiene durch das verfügbare und fachlich passende Icon `mdi-earth`
  ersetzt.
- Der Docker-Build kann dadurch die vorgeschaltete Prüfung
  `scripts/check-mdi-icons.mjs` passieren und anschließend mit Vue-TSC und Vite
  fortfahren.
- Der GitHub-CI-Workflow verwendet für das Frontend nun wie der Docker-Build
  `npm ci`, damit exakt die in `package-lock.json` festgeschriebenen Versionen
  geprüft werden.

## Datenbank und Kompatibilität

- Keine neue Datenbankmigration.
- Alembic-Head bleibt `0028_collected_integration_fixes`.
- Bestehende Daten und Konfigurationen aus 1.1.2 bleiben unverändert.
