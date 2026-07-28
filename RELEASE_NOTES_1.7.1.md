# DocOfHome 1.7.1

Version 1.7.1 führt die Korrekturen aus 1.6.3.6 bis 1.6.3.8 mit dem
Funktionsumfang von 1.7.0 zusammen. Die Zusammenführung wurde als
Drei-Wege-Abgleich gegen 1.6.3.5 durchgeführt, damit keine 1.7-Funktion durch
ältere Dateien überschrieben wird.

## Übernommen aus 1.6.3.6 bis 1.6.3.8

- fehlende und zu niedrige Asset-Codezähler werden per Migration `0046`
  repariert und bei der nächsten Asset-Erstellung zusätzlich selbstheilend
  rekonstruiert;
- neue Hutschienengeräte werden einheitlich als normale DIN-Assets platziert;
  der historische Schutzgerätepfad bleibt für Bestandsdaten erhalten;
- Phasen-/Kammschienen und N-Schienen können FI/RCD- und FI/LS-DIN-Assets
  derselben Verteilung referenzieren;
- eine Schiene speichert entweder den historischen FI/RCD-Verweis oder den
  aktuellen Asset-Verweis;
- ein verknüpftes FI/RCD-DIN-Asset kann erst nach dem Lösen der
  Schienenzuordnung entfernt werden.

## Anpassung der Stromkreis-Pflichtzuordnung

Die in 1.7.0 eingeführte Pflichtzuordnung zu einer konkreten Sicherung wurde an
das aktuelle DIN-Asset-Modell angepasst:

- Sicherungsautomaten, Leitungsschutzschalter, Sicherungen und FI/LS/RCBO aus
  aktiven DIN-Asset-Platzierungen werden als Schutzgerät angeboten;
- historische Sicherungs-, MCB- und RCBO-Datensätze bleiben auswählbar;
- ein eigenständiger FI/RCD ohne Überstromschutz bleibt für einzelne
  Stromkreise unzulässig;
- ein Schutzgerät kann nur einem aktiven Stromkreis zugeordnet werden;
- ein als Stromkreis-Schutzgerät verwendetes DIN-Asset kann nicht aus der
  Verteilung entfernt werden, bevor die Zuordnung geändert wurde;
- Typ, Nennwert, Position und erkennbare Außenleiter werden aus dem gewählten
  DIN-Gerät übernommen.

## Migrationen

Die Migrationskette lautet:

- `0046_repair_asset_code_counters`
- `0047_link_cabinet_rails_to_din_rcd_assets`
- `0048_release_1_7_1`

Die frühere 1.7.0-Migration mit der kollidierenden Revisionsnummer `0046` wurde
auf `0048` verschoben und erweitert. Sie enthält weiterhin Bilder,
Zähler-Capability, feste Portgeschwindigkeiten, Phasenherkunft und
IP-Abgleich sowie zusätzlich den Stromkreisverweis auf ein DIN-Asset.

## Korrektur des Frontend-Builds

- Das in der leeren IP-Übersicht verwendete, in `@mdi/font 7.4.47` nicht
  enthaltene Icon `mdi-ip-off-outline` wurde durch `mdi-ip-outline` ersetzt.
- Der vorangestellte MDI-Icon-Check blockiert den Docker-/Vite-Build dadurch
  nicht mehr.
- Die Asset-Erstellung auf der Smart-Home-Seite verwendet nun den zentralen
  `createEmptyAsset()`-Entwurf und enthält damit alle verpflichtenden
  Bildfelder des Typs `AssetWrite`.
- Home-Assistant-Asset-Entwürfe setzen `image_url`, `image_source` und
  `image_reference` explizit.
- Veraltete Test-Fixtures für `Asset`, `AssetType`, `ElectricalCircuit` und
  `ElectricalConnection` wurden an die erweiterten 1.7-Antwortverträge
  angepasst. Dadurch blockiert `vue-tsc --noEmit` den Build nicht mehr wegen
  fehlender Bild-, Schutzgeräte- oder Phasenherkunftsfelder.

## Update

1. Den vollständigen persistenten `data`-Ordner sichern.
2. Bestehende Container stoppen.
3. Version 1.7.1 in einen neuen, sauberen Ordner entpacken.
4. Image ohne Cache neu bauen.
5. Container starten und das Upgrade bis Alembic-Head `0048` kontrollieren.
6. Browser mit `Strg+F5` vollständig aktualisieren.
7. Stromkreise ohne konkrete Sicherungszuordnung in der Nacharbeitsliste prüfen.

Ein Downgrade sollte nur zusammen mit einem vor dem Update erstellten
Datenbank- und Medienbackup erfolgen.
