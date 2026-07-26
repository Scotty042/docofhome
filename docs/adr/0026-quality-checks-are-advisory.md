# ADR-0026 – Qualitätsprüfungen sind ausschließlich beratend

## Status

Accepted

## Entscheidung

Qualitätsläufe lesen bestehende Daten, speichern nachvollziehbare Befunde und verändern keine
Fachobjekte. Externe Dokumente werden nur über bestehende serverseitige Integrationsgrenzen geprüft.

## Folgen

- Ein Hinweis kann nie versehentlich Benutzerdaten überschreiben.
- Punktwert und Regeln sind transparent und deterministisch.
- Spätere zusätzliche Regeln bleiben additive Produktentscheidungen.
