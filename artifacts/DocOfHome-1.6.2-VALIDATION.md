# DocOfHome 1.6.2 – Validierungsbericht

## Korrektur

- Bei einer Sicherung unter einer Sammel-/Phasenschiene ersetzt die aus Startphase und TE-Position berechnete Außenleiterphase alte gespeicherte L1/L2/L3-Werte vollständig.
- N und PE bleiben erhalten.
- Die Topologieanzeige fällt nicht mehr auf alte gespeicherte Phasen zurück.

## Ausgeführte Prüfungen

- Ruff für alle geänderten Phasen-/Topologiedateien: erfolgreich
- vollständige Phasen- und Topologie-Regressionstests: erfolgreich
- Alembic Upgrade bis Head 0039: erfolgreich
- vollständige Frontendtests: erfolgreich
- npm production build: erfolgreich
- Docker production build: erfolgreich

Die vollständige vorhandene Backend-Suite wurde zusätzlich diagnostisch ausgeführt: 240 Tests bestanden, 15 bereits vorhandene und von dieser Korrektur unabhängige Tests schlugen fehl. Die projektweite mypy-Prüfung bleibt ebenfalls durch Typfehler in unveränderten Bestandsmodulen blockiert.
