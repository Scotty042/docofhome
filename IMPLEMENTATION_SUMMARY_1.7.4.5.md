# Implementation Summary 1.7.4.5

- `CabinetWiringOverlay.vue`: Hausanschluss unten, Zähleranker am Zählerfeld, getrennte FI/RCD-Ports mit IN/OUT-Markern.
- `ElectricalDistributionLayoutPage.vue`: globale Platzierungslisten und Ortsfilter für DIN-Assets und Zähler.
- `ElectricalTopologyPage.vue`: Fallback-Nachladen aller aktiven Schrankkomponenten aus Haupt- und Unterverteilungen.
- Backend: globale Leseendpunkte für aktive Asset- und Zählerplatzierungen.
