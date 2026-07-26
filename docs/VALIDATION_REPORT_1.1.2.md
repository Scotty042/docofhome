# Validierungsbericht – DocOfHome 1.1.2

Stand: 23. Juli 2026

## Prüfumfang

Geprüft wurde das gemeinsame Korrekturrelease für die zehn nach 1.1.1
aufgenommenen Punkte: Zähler-Ort/Asset, Immich-Großansicht, N-/PE-Schienen,
Home-Assistant-Livewerte, Zählerplatzierung, Asset-Typ-Prüfung für Verteilungen,
hierarchische Ortssortierung, Netzanschluss als Quelle, logische
Netzwerkschnittstellen und gerätebezogene Netzwerk-Warnungen.

## Lokal ausgeführte Prüfungen

- Python-Syntaxprüfung für Anwendung, Migrationen, Tests und Hilfsscripte;
- Syntaxprüfung aller TypeScript- und Vue-Scriptblöcke mit dem lokal
  vorhandenen TypeScript-Parser;
- vollständige Alembic-Kette gegen eine neu angelegte lokale SQLite-Datenbank:
  `clean -> 0027 -> 0028 -> 0027 -> head`;
- Prüfung, dass Revision 0028 alle neuen Spalten, Constraints, Fremdschlüssel,
  Indizes und die Tabelle `electrical_meter_placements` anlegt;
- Bestandsdatentest mit einem unter 0027 angelegten Asset, Ort und Stromzähler;
  Daten und Fremdschlüssel blieben über Upgrade, Downgrade und Re-Upgrade erhalten;
- dependency-freier Ausführungstest der hierarchischen Ortssortierung;
- statischer Abnahmecheck für alle zehn Funktionsverträge;
- Versionskonsistenz zwischen `VERSION`, Backend, Frontend und Lockdatei;
- Branding-Prüfung und dependency-freier Quellvertragstest für alle zehn
  gesammelten Punkte;
- vollständige SHA-256-Prüfung aller Manifestdateien nach erneuter Extraktion
  des finalen ZIPs.

## Ergänzte Regressionstests

- Asset-/Ortszuordnung und Ortsfallback eines Verbrauchszählers;
- Speicherung der HA-Entitäten für Gesamtleistung und Spannung;
- zwei halbe N-/PE-Bereiche und Zählerplatzierung im Zählerfeld;
- direkte Platzierung eines Assets vom Typ **Zähler**;
- Verhinderung ungültiger Verteilungs-Assets;
- Netzanschluss als Quelle und Ablehnung als Ziel;
- logische LAN-Bridge, Geräte-IP und neutrale freie Ports;
- hierarchische Sortierung von Etagen und Räumen;
- vollständiger Migrationszyklus der Revision 0028.

## Nicht lokal ausführbare Gates

Die gelieferte ZIP enthält keine installierten Python- oder Node-Abhängigkeiten.
In der strikt lokalen Umgebung waren deshalb vollständige Läufe der
SQLModel-basierten Pytest-Suite sowie von Ruff, mypy, Vue-TSC, Vite, Vitest und
vom MDI-Dateiabgleich nicht möglich. Die zugehörigen Testquellen sind enthalten
und bleiben Bestandteil des normalen Docker-/CI-Builds. Es wurden keine Pakete
oder Abhängigkeiten aus dem Internet nachgeladen.
