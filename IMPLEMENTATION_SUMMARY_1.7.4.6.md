# Implementation Summary 1.7.4.6

Der bisherige endpunktbezogene Filter wurde durch eine verbindungsbezogene Prüfung ersetzt.

## Vorher

Sobald ein Endpunkt den Gerätetyp `mcb` oder `rcbo` hatte, wurden sämtliche Verbindungen dieses Geräts ausgeblendet. Dadurch verschwand auch eine manuell dokumentierte Einspeisung vom Phasenverteilerblock zur Sicherung.

## Jetzt

- `isIndividualCircuitBranch()` blendet nur Verbindungen aus, deren Quelle oder Ziel tatsächlich ein Stromkreis-Endpunkt ist.
- Manuelle Einspeisungen zu LS-/MCB-/RCBO-Geräten bleiben sichtbar.
- Automatische Kammschienenkontakte werden weiterhin separat durch `isAutomaticBusbarContact()` reduziert.
