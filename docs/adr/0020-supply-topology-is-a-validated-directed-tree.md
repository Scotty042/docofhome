# ADR-0020: Versorgungswege bilden einen validierten gerichteten Baum

## Status

Akzeptiert

## Entscheidung

Eine elektrische Verbindung verweist polymorph auf zwei vorhandene Endpunkte und bedeutet
„Quelle versorgt Ziel“. Als Endpunkte dienen nicht verwendete Assets sowie bestehende
Verteilungen, Schutzgeräte und Stromkreise. Die fachliche Identität bleibt im jeweiligen
Bestandsdatensatz; die Topologie erzeugt keine zweite Kopie davon.

Ein Ziel besitzt in dieser Ausbaustufe höchstens eine aktive eingehende Verbindung. Neue oder
geänderte Verbindungen werden auf vorhandene, aktive Endpunkte und auf Zyklen geprüft. Dadurch
entsteht ein gerichteter Wald mit eindeutigem Versorgungsweg und eindeutig ermittelbarer
Wurzel-Einspeisung. Die polymorphen Referenzen werden bewusst in der Service-Schicht validiert,
weil eine einzelne relationale Fremdschlüsselspalte nicht auf vier unterschiedliche Tabellen
verweisen kann.

Phasen und Leiter gehören zur Verbindung, nicht pauschal zum Ziel. Kabeldaten sind optional, da
eine elektrische Verbindung auch durch Einzelader, Sammelschiene oder interne Verdrahtung
realisiert sein kann. Abgeleitete Anzahlen und Einspeisungsnamen werden nicht redundant gespeichert,
sondern bei der Ausgabe aus den aktiven Verbindungen berechnet.

## Folgen

- bestehende Asset- und Elektro-UUIDs bleiben unverändert
- gemeinsame Einspeisung und nachgelagerte Komponenten sind reproduzierbar ableitbar
- archivierte Endpunkte bleiben in vorhandenen historischen Versorgungswegen erkennbar
- Mehrfacheinspeisungen und Umschalter benötigen später ein erweitertes Betriebszustandsmodell
- die Topologie dokumentiert den Bestand und ersetzt keine fachgerechte Planung oder Prüfung
