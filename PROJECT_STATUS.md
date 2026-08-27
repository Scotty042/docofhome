# DocOfHome – Projektstatus

Stand: 27. August 2026

Release: 1.7.13.3

Alembic-Head: `0052`

DocOfHome 1.7.13.3 korrigiert die Rezeptbildpflege: Kamera/Datei und Immich stehen direkt im Editor zur Verfügung, Bilder werden lokal gespeichert. Zusätzlich ist der Abstand zwischen Mengen-/Einheitenangabe und Zutatenname in der Darstellung abgesichert. Keine Datenbankmigration erforderlich.

DocOfHome 1.7.13.1 überarbeitet die Kochbuch-Oberfläche für Desktop und iPad. Lesemodus,
Editor und ein ablenkungsfreier Vollbild-Kochmodus sind nun klar getrennt; Zutaten und
Arbeitsschritte sind touch-tauglich bedienbar. Es ist keine Migration erforderlich; `0052` bleibt aktuell.

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




## Release 1.7.6

- integrierter MCP-Server unter `/mcp` im bestehenden Container;
- Web-Konfiguration mit Aktivierung, öffentlicher Adresse und Token-Rotation;
- Token wird nur gehasht gespeichert;
- Rechte `read`, `write` und `admin`;
- fachlich begrenzte Tools für Bezugsobjekte, Tätigkeiten, Historie und Fälligkeiten;
- keine neue Datenbankmigration, Alembic-Head bleibt `0051`.

## Release 1.7.5

- Alembic-Head `0051`;
- eigene Tätigkeiten-Untermenüs für Bezugsobjekte;
- reine Datums-Historie ohne Uhrzeit;
- Wiederholungen ohne separaten Start-Fälligkeitstermin;
- nächste Fälligkeit aus tatsächlicher Durchführung plus Intervall.

## Release 1.7.4.9

- Alembic-Head `0050`;
- allgemeine Bezugsobjekte für Tätigkeiten und Wartungen;
- rückwirkend pflegbare Durchführungshistorie;
- automatische Tagesabstände sowie Durchschnitt, Minimum und Maximum;
- automatische Historie beim Erledigen;
- Notizen, Kosten, Mess-/Zählerwerte und Anhänge pro Durchführung;
- bestehende Asset-/Orts-/Elektro-Verknüpfungen bleiben erhalten.

## Release 1.7.4.8

- Alembic-Head bleibt `0049`;
- Monatsende berücksichtigt 28, 29, 30 und 31 Tage korrekt;
- frühe Monatsablesungen schließen keine Monatsend-Aufgabe;
- gültige und verspätete Ablesungen werden eindeutig einem Ablesefenster zugeordnet;
- offene Aufgaben bleiben nach Monatswechsel überfällig sichtbar;
- weitere Erinnerungstage sind konkrete Kalendertage;
- Reminder-API und automatischer Aufgabengenerator nutzen eine gemeinsame Logik.

## Release 1.7.4.7

- Alembic-Head bleibt `0049`;
- normale Übersicht erhält eine interaktive Mouse-over-Verkabelung;
- direkte vor- und nachgelagerte Hauptleitungen werden je Gerät selektiv eingeblendet;
- Klick oder Antippen fixiert die Auswahl, Escape hebt sie auf;
- gewählte und verbundene Geräte werden visuell hervorgehoben;
- vollständiger Verkabelungsmodus bleibt unverändert.

## Release 1.7.4.6

- Alembic-Head bleibt `0049`;
- manuelle Einspeisungen zu LS-/MCB-/RCBO-Geräten werden wieder dargestellt;
- ausschließlich Verbindungen zum einzelnen Stromkreis-Endpunkt bleiben ausgeblendet;
- automatische Kammschienen-Einzelkontakte bleiben visuell reduziert;
- Schutzgeräte können dadurch als Teil der Hauptverkabelung sichtbar bleiben.

## Release 1.7.4.4

- Alembic-Head bleibt `0049`;
- Anschlusspunkte an Geräten und Schienen werden abhängig von der Leitungsrichtung oben oder unten gewählt;
- Verbindungen zu oberhalb liegenden Sammelschienen steigen direkt nach oben auf;
- von unten kommende Leitungen enden sauber an der Unterkante von Sicherungen, Schienen und Komponenten;
- freie orthogonale Leitungsführung innerhalb der Schrankdarstellung bleibt erhalten.

## Release 1.7.4.3

- Alembic-Head bleibt `0049`;
- freie orthogonale Leitungsführung innerhalb der Schrankdarstellung wiederhergestellt;
- keine erzwungene Führung über obere Feldränder;
- alle Hauptverbindungen bleiben vollständig sichtbar;
- L1, L2, L3, N und PE erhalten auf horizontalen und vertikalen Abschnitten festen Abstand;
- einzelne Stromkreise und ihre LS-/RCBO-Abgänge bleiben ausgeblendet.

## Release 1.7.4.2

- Alembic-Head bleibt `0049`;
- Verkabelungsansicht auf Hauptkomponenten und Hauptversorgungswege reduziert;
- schmale LS-/RCBO-/Ein-TE-Nebenabgänge ausgeblendet;
- Leitungsführung über Feldränder und definierte Korridore;
- doppelte Hauptverbindungen visuell gebündelt;
- externe Ein- und Ausgänge feldnah positioniert.

## Release 1.7.4

- Alembic-Head bleibt `0049`;
- Umschaltung zwischen kompakter Übersicht und visueller Verkabelung;
- farbige Leiterlinien für L1, L2, L3, N und PE direkt in der Schrankansicht;
- Dreieck für Hausanschluss sowie Kreis/Viereck für externe Abgänge;
- reduzierte Darstellung automatischer Kamm-/Sammelschienenkontakte;
- vor- und nachgelagerte Verbindungen in den Geräte- und Komponentendetails;
- kontrastreiche Phasen-Chips mit vollflächiger Farbe und weißer Schrift;
- vollständige und beschriftete Reihenzähler ohne schwebende Null-Badges;
- kompakte N-/PE-Schienen ohne eingeblendete Verkabelungsdetails.

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
