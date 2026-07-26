# DocOfHome 1.2.0

DocOfHome 1.2.0 setzt die vollständige Aufgabenübergabe auf Basis von 1.1.3 um
und konzentriert sich auf große Home-Assistant-Installationen, bessere
Asset-Workflows und eine fachlich genauere Zählerschrankdarstellung.

## Höhepunkte

- sofort bedienbare HA-Oberfläche ohne Tausende gleichzeitig gerenderte Entitäten
- 50 Geräte beziehungsweise 100 Entitäten pro serverseitig gefilterter Seite
- ein gebündelter HA-Sync, 15 Minuten Registercache und 30 Sekunden Livecache
- mehrere HA-Geräte und Entitäten je Asset mit Rollen
- Smart Meter und andere DIN-Produkte mit TE-Breite und Livewert im Schrank
- N und PE auf derselben Ebene links/rechts
- Produktbilder per Upload, Immich, optionaler Wikimedia-Suche oder URL
- Assets duplizieren oder als nummerierte Serie mit optionaler TE-Platzierung anlegen
- Labels direkt im Asset-Formular erstellen
- seltene Navigationseinträge unter **Mehr**

## Update

Vor dem Update ein DocOfHome-Backup und eine externe Kopie des gesamten
persistenten `data`-Ordners erstellen. Beim Start migriert Alembic von `0028`
auf `0029`. Details stehen in `docs/MIGRATION_GUIDE_1.2.0.md`.

## Kompatibilität

Alle in 1.1.0 bis 1.1.3 eingeführten Funktionen bleiben erhalten. Bestehende
HA-Zuordnungen, Zähler, Elektro- und Netzwerkdaten, Produktbilder, Labels und
Dokumentverknüpfungen werden nicht gelöscht. Das PE-Icon bleibt `mdi-earth`.
