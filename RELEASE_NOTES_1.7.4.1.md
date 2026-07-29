# DocOfHome 1.7.4.1

## Ziel

Version 1.7.4.1 überarbeitet die in 1.7.4 eingeführte visuelle
Verkabelungsansicht. Der Modus konzentriert sich nun auf die Hauptverteilung
und trennt parallele Leitungen klarer voneinander.

## Reduzierte Hauptverkabelung

Die Schrankansicht zeigt bewusst keine Verkabelung einzelner Stromkreise mehr.
Ausgeblendet werden:

- Stromkreis-Endpunkte;
- Verbindungen zu LS-/MCB- und FI/LS-/RCBO-Geräten einzelner Stromkreise;
- ältere als Sicherung modellierte Abzweige, wenn sie unmittelbar in einen
  Stromkreis führen.

Die vollständige Dokumentation bleibt in der Versorgungstopologie sowie in den
vor- und nachgelagerten Verbindungen der Detailansichten erhalten.

Sichtbar bleiben insbesondere Hausanschluss, Vorsicherungen, Zähler,
Phasenverteiler, FI/RCD, Sammel- und Kammschienen, N-/PE-Schienen,
Unterverteilungen und externe Hauptabgänge.

## Verbesserte Linienführung

- Verbindungen erhalten getrennte horizontale Kabelkanäle statt einer
  wiederholten Modulo-Zuordnung auf dieselben Spuren.
- Mehrere Verbindungen an demselben Gerät werden an getrennten Anschlusspunkten
  aufgefächert.
- Leiter einer mehradrigen Verbindung bleiben als paralleles Bündel sichtbar.
- Eine dunkle Kontur unter jeder Leitung trennt Kreuzungen und dicht
  nebeneinanderliegende Leiter optisch.
- Die Linienbreite wurde reduziert, damit Gerätebeschriftungen weniger verdeckt
  werden.

## Datenbank und Update

- Alembic-Head bleibt `0049`.
- Es ist keine neue Datenbankmigration erforderlich.
- Bestehende elektrische Verbindungen werden nicht verändert oder gelöscht;
  ausschließlich die Darstellung im Schrankmodus wurde angepasst.
