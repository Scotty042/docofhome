# ADR 0021 – Eingebettete Versorgungsinformationen verwenden die abgeleitete Topologie

## Status

Akzeptiert.

## Kontext

Phasen und nachgelagerte Komponenten sollen direkt im Verteiler und am Schutzgerät sichtbar sein.
Die Verbindungen werden bereits zentral als gerichteter Versorgungsbaum gespeichert und vom Backend
validiert. Eine zusätzliche Speicherung an Sicherungen würde widersprüchliche Angaben ermöglichen.

## Entscheidung

Alle eingebetteten Übersichten lesen ausschließlich den bestehenden Topologie-Endpunkt. Die UI
ermittelt die eingehende Verbindung anhand des Zielschlüssels und zeigt die bereits vom Backend
abgeleiteten Wurzel-Einspeisungen und Nachfolgerzahlen. Direkte Aktionen verweisen mit einem
Endpunktschlüssel auf die zentrale Topologie. Bei einem unverbundenen Ziel öffnet dieselbe Seite
den regulären Anlagedialog mit vorbelegtem Ziel.

## Folgen

- Phase, Quelle und Nachfolger bleiben in allen Ansichten konsistent.
- Es ist keine Migration und kein zusätzlicher Schreibendpunkt erforderlich.
- Änderungen an der Verkabelung sind nach dem erneuten Laden überall sichtbar.
- Ist die Topologie vorübergehend nicht erreichbar, bleiben Verteiler und Schutzgeräte bearbeitbar;
  lediglich die eingebettete Übersicht zeigt einen Warnhinweis.
