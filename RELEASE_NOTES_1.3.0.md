# DocOfHome 1.3.0

DocOfHome 1.3.0 erweitert die elektrische Schrankdokumentation um passive,
nicht als Asset geführte Schrankkomponenten und behebt die Platzierung in
Unterverteilungen mit einfacher Reihenaufteilung.

## Neue Schrankkomponenten

In einer Haupt- oder Unterverteilung können jetzt folgende passive Komponenten
angelegt und auf einer DIN-Schiene positioniert werden:

- Phasenverteilerblock;
- Sammelschiene und Phasenschiene;
- N- und PE-Schiene;
- Reihen- und Anschlussklemme;
- Potentialverteiler;
- sonstige passive Schrankkomponente.

Jede Komponente erhält Bezeichnung, Reihe, TE-Startposition, TE-Breite und die
zugehörigen Leiter `L1`, `L2`, `L3`, `N` und/oder `PE`. Optional können
Bemessungsstrom, maximaler Leiterquerschnitt, Zahl der Abgänge, Beschreibung und
Notizen dokumentiert werden. Die Komponenten sind bewusst keine Assets.

## Verkabelung und Versorgungstopologie

Schrankkomponenten stehen als eigener Endpunkttyp `cabinet_component` in der
Elektro-Verkabelung zur Verfügung. Dadurch lässt sich beispielsweise folgender
Versorgungsweg dokumentieren:

`Netzanschluss → Vorsicherung → Zähler → Phasenverteilerblock → Unterverteilungen / PV / Sammelschiene`

Verkabelte Komponenten können erst archiviert werden, wenn ihre Verbindungen
entfernt wurden. Bestehende Asset-, Verteilungs-, Schutzgeräte- und
Stromkreis-Endpunkte bleiben unverändert.

## Reihenaufteilung und Unterverteilungen

- Schutzgeräte lassen sich auch bei Verteilungen im Modus **Einfache Reihen**
  per Drag-and-drop auf Reihe und TE-Position verschieben.
- DIN-Assets und passive Schrankkomponenten können ebenfalls in einer einfachen
  Reihenaufteilung platziert werden.
- Die Serienanlage verlangt bei einer einfachen Reihenaufteilung keinen
  DIN-Bereich mehr. Ein DIN-Bereich wird nur im Feld-/Bereichsmodus angezeigt
  und übertragen.
- Überschneidungen zwischen Schutzgeräten, DIN-Assets und Schrankkomponenten
  werden serverseitig und in der Oberfläche verhindert.

## Datenbank

Migration `0031_cabinet_components_and_rows_placements`:

- legt die Tabelle `electrical_cabinet_components` an;
- erlaubt `NULL` bei `electrical_asset_placements.area_id`, damit DIN-Assets in
  einfachen Reihen platziert werden können;
- erweitert die zulässigen Elektro-Endpunkttypen um `cabinet_component`.

Vor dem Update ist ein vollständiges Backup des persistenten `data`-Ordners zu
erstellen.
