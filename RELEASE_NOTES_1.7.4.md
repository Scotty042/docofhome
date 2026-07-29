# DocOfHome 1.7.4

## Ziel

Version 1.7.4 verbessert die Schaltschrankdarstellung und bündelt technische
Verkabelungsinformationen dort, wo sie benötigt werden: als visuelle Ebene in
der Übersicht und als strukturierte Liste in den Details.

## Neue Verkabelungsansicht

Die bisherige Umschaltung **Kompakt / Erweitert** wurde ersetzt durch:

- **Übersicht** – kompakte, aufgeräumte Schrankdarstellung;
- **Verkabelung** – dieselbe Schrankdarstellung mit dynamisch berechneten
  Leiterlinien.

Die Linien werden nicht statisch gespeichert. Sie werden aus der vorhandenen
elektrischen Topologie und den sichtbaren Positionen der DIN-Geräte,
Schrankkomponenten sowie Schienen erzeugt.

### Farblogik

- L1: Rot
- L2: Schwarz mit Kontrastkante
- L3: Hellgrau
- N: Blau
- PE: Grün beziehungsweise grün-gelb gestrichelt

### Symbole

- Der Netz-/Hausanschluss erscheint als Dreieck.
- Eine Leitung, die den aktuellen Verteiler verlässt, endet an einem Kreis.
- Eine nachgelagerte Verteilung beziehungsweise Unterverteilung wird als
  Viereck dargestellt.

Automatisch erzeugte Einzelkontakte einer Phasen-/Kammschiene zu jedem
überdeckten DIN-Gerät werden nicht zusätzlich als einzelne Linie gezeichnet.
Die Schiene selbst zeigt bereits die Verteilung; ihre Einspeisung wird je
Leiter einmal dargestellt.

## Kompakte Schienen

N- und PE-Schienen zeigen in der normalen Übersicht keine vollständige
Verkabelungszusammenfassung mehr. Name, Typ, Leiter und optionale FI-Zuordnung
bleiben sichtbar. Weitere Informationen stehen in der Detailansicht und in der
Verkabelungsansicht bereit.

## Vor- und nachgelagerte Verbindungen

Die Detailansichten von Schutzgeräten, DIN-Assets und Schrankkomponenten
enthalten jetzt zwei eigene Bereiche:

- **Vorgelagerte Verbindungen** – woher das Element versorgt wird;
- **Nachgelagerte Verbindungen** – welche Elemente weiter versorgt werden.

Jeder Eintrag zeigt verbundenes Objekt, Objekttyp, Verbindungsart, optionale
Leitungsdaten sowie die wirksamen Leiter. Der Eintrag öffnet den betreffenden
Endpunkt direkt in der Versorgungstopologie.

## Lesbarkeit und Reihenzähler

- L1/L2/L3/N/PE-Chips besitzen einen vollflächigen Hintergrund und eine deutlich
  kontrastierende weiße Schrift.
- Die bisher teilweise schwebende `0` war die Anzahl der Schutzgeräte und
  berücksichtigte DIN-Assets sowie Schrankkomponenten nicht. Der Zähler umfasst
  jetzt alle sichtbaren Elemente einer Reihe, ist als „Elemente“ beschriftet
  und wird bei leerer Reihe nicht angezeigt.

## Datenbank und Update

- Alembic-Head bleibt `0049`.
- Es ist keine neue Datenbankmigration erforderlich.
- Vor dem Update weiterhin den persistenten Datenordner und die Medien sichern.
