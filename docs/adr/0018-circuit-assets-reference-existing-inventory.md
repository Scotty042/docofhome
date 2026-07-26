# ADR-0018: Stromkreise referenzieren bestehende Assets

## Status

Akzeptiert

## Entscheidung

Ein Stromkreis kann mehrere bereits vorhandene Assets über eine eigene, historisierbare
Zuordnungstabelle referenzieren. Das Asset bleibt die einzige Quelle für Name, docofhome-Code,
Typ, Standort und Lebenszyklus. Ein Stromkreis erzeugt weder ein zweites Geräteobjekt noch eine
zweite Standortzuordnung.

Das Entfernen beendet nur die aktive Verbindung. Der Datensatz erhält einen Zeitstempel und kann
für spätere Historienansichten gelesen werden. Eine neue Zuordnung desselben Assets erzeugt einen
neuen Datensatz. Aktive Duplikate verhindert die Datenbank zusätzlich zur Anwendungsprüfung.

## Folgen

- ein Asset darf bei Bedarf mehreren Stromkreisen zugeordnet sein, etwa bei mehrphasigen oder
  virtuell zusammengefassten Versorgungen
- archivierte Assets bleiben in bestehenden Stromkreis-Dokumentationen erkennbar
- archivierte Stromkreise sind unveränderlich, ihre Zuordnungen bleiben jedoch lesbar
- es findet keine automatische Zuordnung nach Standort oder Asset-Typ statt
- die Funktion dokumentiert den Bestand und ersetzt keine fachgerechte Elektroplanung
