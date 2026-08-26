# Validierung DocOfHome 1.7.7

## Ausgeführt

- Versionsvertrag und JSON-Manifest geprüft.
- Python-3.12-Syntax der neuen/angepassten Backend-, Schema- und Migrationsdateien geprüft.
- TypeScript-/Vue-Syntaxprüfung des vorhandenen Projekts ausgeführt.
- Statische Release- und Migrationsverträge für 1.7.7 geprüft.
- Release-ZIP nach Erstellung mit `unzip -t` geprüft und SHA-256 ermittelt.

## Einschränkungen

- Der vollständige Backend-Testlauf konnte in der lokalen Desktop-Umgebung nicht
  abgeschlossen werden, weil die isolierte Abhängigkeitsinstallation beim nativen
  `cryptography`-Build nicht innerhalb des verfügbaren Lauffensters fertig wurde.
- Frontend-Test und Vite-Produktionsbuild konnten nicht abgeschlossen werden, weil
  der Paketmanager einen Neuaufbau von `node_modules` verlangte und nach dem ersten
  Downloadlauf im eingeschränkten Netz nicht alle Tarballs erneut erreichbar waren.
- Ein echter SWAG-, Docker- und Chrome-PWA-Installationstest benötigt die Zielumgebung.

Diese Einschränkungen sind keine als bestanden deklarierten Tests. Das Dockerfile
behält die bestehenden Build-/Importprüfungen aus 1.7.6 bei.
