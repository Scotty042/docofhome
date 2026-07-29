# DocOfHome 1.7.4.2

## Schematische Hauptverkabelung

Version 1.7.4.2 reduziert die Verkabelungsansicht auf einen verständlichen
Versorgungsplan. Die vollständige gespeicherte Topologie bleibt unverändert und
ist weiterhin in den Detail- und Topologieansichten verfügbar.

### Änderungen

- einzelne Stromkreise sowie schmale LS-/RCBO- und Ein-TE-Abgänge werden in der
  Schrankgrafik nicht mehr gezeichnet;
- historische einpolige Sicherungen werden zusätzlich über ihre tatsächliche
  Kartenbreite als Nebenabgang erkannt;
- mehrere gleichgerichtete Verbindungsdatensätze zwischen denselben
  Hauptkomponenten werden zu einer visuellen Leitung gebündelt;
- Verbindungen innerhalb eines Feldes verlaufen über einen seitlichen
  Routing-Korridor;
- Verbindungen zwischen Feldern werden über die oberen Feldränder geführt;
- lange Leitungsabschnitte verlaufen damit nicht mehr mitten durch DIN-Geräte,
  Zählerfelder oder Gerätekarten;
- externe Ein- und Ausgänge werden nahe am zugehörigen Feld platziert, statt
  Leitungen bis zum unteren Ende der gesamten Seite zu verlängern;
- Linien und Konturen wurden zurückhaltender dimensioniert.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0049`.
