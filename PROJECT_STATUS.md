# DocOfHome – Projektstatus

Stand: 28. Juli 2026

Release: 1.7.3

Alembic-Head: `0049`

DocOfHome 1.7.3 korrigiert die Bewertung getrennter Leiterwege an einem
gemeinsamen Ziel. Eine N- oder PE-Einzelleiterverbindung bleibt auf ihrer
eigenen Verbindung wirksam und übernimmt nicht länger die L1/L2/L3-Versorgung
aus einem parallelen Pfad. Die Gesamtversorgung des Zielgeräts wird weiterhin
als Vereinigung aller eingehenden Verbindungen dargestellt.

## Verbindliche Elektro-Logik

- Eine **Phasenschiene/Kammschiene** ist eine positionsabhängige physische
  Verbindung zu vollständig überdeckten Schutzgeräten. Ihre abgeleiteten
  Verbindungen werden automatisch erzeugt, aktualisiert und archiviert.
- Eine allgemeine **Sammelschiene** bleibt ein manuell dokumentierter
  Verteilpunkt und erzeugt keine automatische TE-Phasenfolge.
- Pro Schutzgerät kann nur eine vollständig überdeckende Phasenschiene
  phasenbestimmend sein. Teilüberdeckungen und konkurrierende Schienen werden
  abgewiesen.
- Die wirksame Außenleiterphase wird aus Startphase, Schienenposition,
  Geräteposition, Gerätetyp und Polzahl berechnet und kann nicht manuell
  überschrieben werden.
- FI/RCD-Zuordnungen an Phasenschienen sind optional. N-Schienen dürfen nur
  fachlich passende FI-Gruppen referenzieren; PE-Schienen bleiben davon
  unabhängig.
- Stromkreise übernehmen die wirksame Phase ihrer Einspeisung und geben sie an
  nachgelagerte Verbraucher weiter.
- Smart-Meter-Messpunkte dürfen nur einen Leiter messen, der auf der wirksamen
  Verbindung tatsächlich vorhanden ist; bei eindeutig einphasigen
  Verbindungen wird die Phase automatisch gesetzt.

## Lebenszyklus und Datenintegrität

- Schutzgeräte, Stromkreise, Schrankkomponenten und allgemeine Assets können
  nicht archiviert oder fachlich umgewandelt werden, solange aktive manuelle
  Verkabelungen oder abhängige Beziehungen bestehen.
- Automatisch verwaltete Kammschienen-Verbindungen sind von manuellen
  Topologiebeziehungen getrennt und schreibgeschützt.
- Ein Typwechsel oder die Archivierung einer N-Schiene ist gesperrt, solange
  Schutzgeräte sie referenzieren.
- Layoutwechsel sind gesperrt, solange aktive Felder, Bereiche oder platzierte
  Komponenten dem Zielaufbau widersprechen.
- Migration `0043` normalisiert Schienenleiter, repariert eindeutige
  Phasenschienen-Beziehungen, Messphasen und nachgelagerte Außenleiter, ohne
  manuelle allgemeine Sammelschienen-Verkabelungen umzudeuten.

Vor jedem Update ist ein vollständiges Backup des persistenten `data`-Ordners
erforderlich. Details stehen in `RELEASE_NOTES_1.6.3.md`.

## Korrektur 1.6.3.8

- per Migration angelegte Asset-Typen erhalten fehlende Nummernkreise;
- der Asset-Typ **Smartes Relais / DIN-Schaltaktor** kann wieder Codes wie
  `SRA-001` vergeben;
- Migration `0046` korrigiert fehlende und zu niedrige Einträge in
  `asset_code_counters`;
- die Laufzeit-Codevergabe rekonstruiert einen fehlenden Zähler zusätzlich
  selbstheilend aus vorhandenen Asset-Codes.




## Release 1.7.3

- Alembic-Head bleibt `0049`;
- direkte N-/PE-Einzelleiterwege zu FI/RCD, Schutzgerät, Asset oder Stromkreis
  erben keine Außenleiter aus parallelen Einspeisungen;
- Verbindungsebene und aggregierte Geräteversorgung werden getrennt bewertet;
- gültige Kombination „L1/L2/L3 über Phasenverteilerblock, N direkt vom
  Netzanschluss“ erzeugt keine Abweichungswarnung;
- der Verbindungsdialog erlaubt den bewussten Wechsel von einer
  Außenleiterverbindung zu einem reinen N-/PE-Weg.

## Release 1.7.2

- Migrationskette bis `0049`;
- vorhandene aktive N-/PE-Schienenbereiche werden automatisch als echte
  Schrankkomponenten und Topologie-Endpunkte materialisiert;
- neu angelegte N-/PE-Bereiche erzeugen ihren verkabelbaren Endpunkt direkt;
- N-Schienen führen ausschließlich `N`, PE-Schienen ausschließlich `PE`;
- reine N-/PE-Verbindungen erben keine Außenleiterphase;
- FI/RCD → N-Schiene sowie getrennte N-/PE-Abgänge sind dokumentierbar;
- direkte Verbindungen zwischen N- und PE-Schiene werden verhindert.

## Release 1.7.1

- Migrationskette bis `0048`;
- Asset-Codezähler-Reparatur aus 1.6.3.6;
- vereinheitlichtes DIN-Gerätemodell aus 1.6.3.7;
- FI/RCD-DIN-Asset-Zuordnung aus 1.6.3.8;
- vollständiger 1.7-Funktionsumfang für Elektro, Zähler, Netzwerk, Bilder,
  Aufgaben und kompaktere Oberflächen;
- Pflicht-Sicherungszuordnung für aktuelle DIN-Assets und historische
  Schutzgeräte.
