# DocOfHome 1.0.0 – Release Notes

DocOfHome 1.0.0 ist die erste stabile Version des lokalen digitalen
Hauszwillings. Der Schwerpunkt liegt auf vollständiger technischer
Dokumentation, updatefähiger Datenhaltung und optionalen, eng begrenzten
Integrationen.

Die Version ergänzt ein konfigurierbares Dashboard, mobile
Zählerstandserfassung, Monats-/Jahresvergleiche, Kalenderwartungen,
Ableseerinnerungen, globale Inventarnummern, erweiterte Netzwerkdokumentation,
read-only FRITZ!Box-Vorschläge, logische Workloads, Datenportabilität,
Änderungshistorie und einen geführten Fachassistenten.

Vor dem Update ist ein lokales und extern gesichertes Backup erforderlich. Die
Migrationen 0024 bis 0026 werden beim Containerstart automatisch angewendet.
Die finale Paketfassung kann Migration 0024 außerdem sicher fortsetzen, wenn
ein zuvor abgebrochener SQLite-Batchlauf eine `_alembic_tmp_*`-Arbeitstabelle
hinterlassen hat; manuelle Eingriffe in die Datenbank sind dafür nicht nötig.

DocOfHome 1.0 besitzt keine Authentifizierung und darf ausschließlich in einem
vertrauenswürdigen privaten Netzwerk betrieben werden.

## Aktualisierter Fixstand

Dieser weiterhin als Version 1.0.0 geführte Stand ergänzt Verbindungstests direkt im Erst-Setup, FRITZ!Box-Unterstützung, die geführte Etagen-/Raumerfassung, Immich-Berechtigungshinweise, eine visuelle Immich-Bildauswahl, die korrigierte Home-Assistant-Geräteanzeige und ein eigenes Browser-Icon.

## Fixstand 2

Der zweite 1.0.0-Fixstand verbessert Bedienbarkeit und Nachvollziehbarkeit: Gebäudestrukturen lassen sich nach dem Erst-Setup weitergeführt bearbeiten, die globale Suche erhält einen zuverlässigen Fokus und das alternative Kürzel `/`, Dashboard-Kacheln werden direkt per Drag-and-Drop sortiert, FRITZ!Box-Geräte erscheinen im Netzwerkmodul, die Änderungshistorie zeigt verständliche Vorher-/Nachher-Werte und bestehende Assets werden im Assistenten über eine Suchliste ausgewählt.

Die Datenbankstruktur und die Produktversion bleiben unverändert.
