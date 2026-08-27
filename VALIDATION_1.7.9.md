# Validierung DocOfHome 1.7.9

## Ausgeführt

- DocOfHome 1.7.8 als unveränderte Release-Basis kopiert und auf 1.7.9 fortgeführt.
- Versionsvertrag, Branding, Syntax der erweiterten MCP-Datei und statischer Releasevertrag geprüft.
- Registrierungs- und Berechtigungsverträge für alle neuen MCP-Domänen ergänzt.
- Nach Docker-Lauf 33051360742 unmaskierte Backticks im TypeScript-Handbuch korrigiert und
  den vollständigen MCP-Template-String auf weitere unmaskierte Begrenzungszeichen geprüft.
- Release-ZIP nach Erstellung vollständig mit `unzip -t` geprüft und SHA-256 ermittelt.

## Einschränkungen

- Vollständige Backendtests sind lokal nicht ausführbar, da pytest und die Python-3.12-Projektabhängigkeiten fehlen.
- Frontendtests und Vite-Build sind lokal nicht ausführbar, da Node.js/npm fehlen.
- Fachliche MCP-Integrationstests benötigen eine migrierte Testdatenbank in der Ziel-/CI-Umgebung.

Diese Einschränkungen werden nicht als bestandene Tests ausgewiesen.
