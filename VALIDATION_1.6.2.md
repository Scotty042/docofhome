# DocOfHome 1.6.2 – Validierungsbericht

Stand: 27. Juli 2026

## Gegenstand dieser Korrektur

Die Phasen-/Kammschiene war im Schrankplan zwar sichtbar, ihre physisch zwingenden
Kontakte zu den überspannten Sicherungsautomaten mussten aber weiterhin manuell als
Versorgungsverbindungen angelegt werden. Außerdem wurde eine fehlende FI/RCD-Zuordnung
fälschlich als Warnung dargestellt, obwohl Kammschienen auch ohne FI/RCD eingesetzt
werden können.

## Umsetzung

- Neue zentrale Synchronisierung `PhaseRailConnectionService`.
- Beim Anlegen oder Ändern einer Phasen-/Kammschiene werden Verbindungen zu allen
  bereits platzierten und überspannten Schutzgeräten automatisch angelegt.
- Wird ein Schutzgerät später unter der Schiene platziert oder verschoben, wird die
  Verbindung automatisch erstellt, korrigiert oder archiviert.
- Die Außenleiterphase wird ausschließlich aus Startphase, Schienenstart und
  TE-Position berechnet.
- Direkte automatische Schienenverbindungen enthalten nur L1/L2/L3. N und PE werden
  separat dokumentiert.
- Automatische Schienenverbindungen können in der Topologie weder gelöscht noch auf
  andere Endpunkte oder Verbindungsarten umgehängt werden.
- Eine FI/RCD-Zuordnung ist bei einer Phasen-/Kammschiene optional. Die bisherige
  Warnung bei fehlender Zuordnung wurde entfernt und der Dialogtext klargestellt.
- Migration `0042` legt fehlende Verbindungen für bestehende Installationen an,
  korrigiert falsche Phasen und archiviert veraltete beziehungsweise umgekehrte
  direkte Schienenverbindungen.

## Erfolgreiche Prüfungen

- Python-Syntaxprüfung der Anwendung, Migrationen, Tests und Prüfscripte
- TypeScript-Syntaxprüfung der geänderten Vue-/Test-Scripte mit dem lokalen
  TypeScript-Parser
- Versions- und Brandingprüfung
- gesammelte Korrekturverträge und Releasevertrag 1.6.2
- dependency-freier Phasenschienen-Vertragstest
- ZIP-Kompressions- und Extraktionsprüfung

## Nicht vollständig ausgeführte Gates

Die vollständige Python-Test- und Alembic-Suite konnte in dieser Umgebung nicht
abhängigkeitsbasiert ausgeführt werden, weil die erforderlichen Python-Pakete nicht
über den Paketindex verfügbar waren. `npm ci` konnte ebenfalls nicht vollständig
abgeschlossen werden; deshalb wurden Vue-TSC, Vite und Vitest nicht vollständig
neu ausgeführt. Die entsprechenden Regressionstests und Prüfscripte sind im Paket
enthalten.

## Alembic-Head

`0042`
