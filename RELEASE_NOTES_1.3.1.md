# DocOfHome 1.3.1

DocOfHome 1.3.1 korrigiert die DIN-Schienenansicht, erweitert die
DIN-Breitenlogik und macht Mehrfacheinspeisungen an passiven
Schrankkomponenten fachlich prüfbar. Außerdem wird der laufende
Verbrauchsmonat nur noch bis heute bewertet.

## DIN-Assets direkt auf der Hutschiene

Normale Assets mit einer wirksamen DIN-Breite – beispielsweise Smart Meter –
werden jetzt gemeinsam mit Schutzgeräten und passiven Schrankkomponenten im
TE-Raster dargestellt. Ein platzierter Smart Meter mit vier TE belegt damit
sichtbar vier zusammenhängende Modulplätze statt unterhalb der Schiene zu
erscheinen.

Auf breiten Desktop-Ansichten können Schutzgeräte und normale DIN-Assets per
Drag-and-drop innerhalb einer Reihe sowie zwischen Reihen und Gerätebereichen
verschoben werden. Die Kollisionsprüfung berücksichtigt alle drei Objektarten.
Auf Touchgeräten bleibt der Positionsdialog der verlässliche Bedienweg.

## DIN-Breite ohne Produktpflicht

Eine optionale DIN-Breite kann jetzt direkt hinterlegt werden:

1. am einzelnen Asset;
2. an einem DIN-Produkt;
3. als Standard am Asset-Typ.

Die Reihenfolge der wirksamen Breite ist **Asset vor Produkt vor Asset-Typ**.
Damit können Typen wie Sicherungsautomat, FI-Schalter, FI/LS-Schalter oder Smart
Meter eine typische TE-Breite mitbringen, ohne dass zuvor zwingend ein
Produktstammsatz angelegt werden muss. Schutzgeräte übernehmen diese Breite
automatisch in Editor, Positionsdialog und Drag-and-drop. Nur Assets mit einer
wirksamen DIN-Breite werden in der Oberfläche als neu platzierbare DIN-Geräte
angeboten. Bereits vorhandene Schutzgerätebreiten bleiben aus Gründen der
Rückwärtskompatibilität verwendbar.

## Mehrere Einspeisungen und Phasenprüfung

Ein Phasenverteilerblock oder eine andere passive Schrankkomponente kann mehrere
gleichzeitige eingehende Verbindungen besitzen. So lassen sich beispielsweise
Netz-/Zählerpfad und PV-Wechselrichter als zwei dokumentierte Einspeisungen
desselben Blocks abbilden. Die Oberfläche zeigt alle eingehenden Verbindungen
und deren gemeinsame Leiter an.

Für Schrankkomponenten gelten nun folgende Prüfungen:

- jede Verbindung führt ihre ausgewählten Leiter unverändert von Quelle zu Ziel;
- `L1` kann nicht stillschweigend als `L2` weitergeführt werden;
- eine Komponente darf nur Leiter verwenden, die in ihrer Konfiguration
  freigegeben sind;
- ausgehend dürfen nur Leiter verwendet werden, die über mindestens eine der
  aktiven Einspeisungen tatsächlich anliegen;
- das Ändern oder Löschen einer Einspeisung wird abgelehnt, wenn dadurch bereits
  dokumentierte Abgänge nicht mehr versorgt wären.

## Laufender Verbrauchsmonat

Der Zeitraum **Aktueller Monat** endet jetzt bei „heute“ statt am ersten Tag des
Folgemonats. Eine Ablesung am aktuellen Tag gilt für diesen laufenden Zeitraum
als ausreichende Endabdeckung; eine sekundengenaue Ablesung zum aktuellen
Zeitpunkt oder eine Ablesung aus der Zukunft wird nicht mehr verlangt.
Historische, abgeschlossene Zeiträume behalten ihre strenge
Vollständigkeitsprüfung.

## Datenbank

Migration `0032_asset_and_type_din_width` ergänzt optionale, validierte
`module_width`-Felder bei Asset-Typen und Assets. Bestehende Datensätze erhalten
`NULL` und werden nicht fachlich umgeschrieben.

## Build-Korrektur

Die Initialisierung des Asset-Formulars auf der Home-Assistant-Seite enthält
nun ebenfalls das mit 1.3.1 eingeführte Feld `module_width`. Dadurch ist das
Formular wieder vollständig mit dem TypeScript-Typ `AssetWrite` kompatibel und
`vue-tsc --noEmit` bricht nicht mehr mit TS2345 ab.
