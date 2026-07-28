# DocOfHome 1.6.3.4

## Kammschienen-Automatik: geerbte DIN-Breiten

Die Laufzeitdaten des Anwenders zeigten, dass der explizite Synchronisations-Endpunkt
erfolgreich aufgerufen wurde, aber weiterhin null Schutzgeräte erkannte. Der Grund war
eine unterschiedliche Breitenlogik:

- Die Verteilerschrankansicht verwendet die wirksame DIN-Breite vom Asset, Produkt oder
  Asset-Typ, wenn `electrical_protective_devices.module_width` bei älteren Datensätzen leer ist.
- Die automatische Kammschienen-Verkabelung prüfte bislang nur die lokale Spalte des
  Schutzgeräts und verwarf solche sichtbar platzierten Geräte.

Die Implementierung nutzt dafür `effective_asset_module_width`.

1.6.3.4 verwendet für Erkennung, vollständige TE-Überdeckung, Phasenberechnung und
Verifikation exakt dieselbe Vererbungskette wie die Schrankansicht.

### Ergebnis

Für vollständig überdeckte Schutzgeräte wird automatisch erzeugt:

- Quelle: Phasen-/Kammschiene
- Ziel: Schutzgerät
- Verbindungsart: Sammelschiene/Phasenschiene
- Außenleiter: gemäß Startphase und TE-Position

Allgemeine DIN-Assets bleiben weiterhin unverbunden. Im Serverlog wird jeder explizite
Synchronisationslauf mit Anzahl übermittelter, erkannter und abgelehnter Geräte protokolliert.

Alembic bleibt auf Revision `0044`; die Laufzeitkorrektur repariert Bestandsdaten beim
Speichern der Schiene oder beim Öffnen der Topologie.
