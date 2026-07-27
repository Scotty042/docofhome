# DocOfHome 1.6.2 – Aufgaben-, Phasen- und Paketkorrekturen

Veröffentlicht: 27. Juli 2026

DocOfHome 1.6.2 baut auf Version 1.6.1 auf und schließt die im Korrektur-Runbook
noch offenen Integritäts- und Bedienlücken. Bestehende Daten werden nicht
stillschweigend umgeschrieben.

## Wichtigste Änderungen

- Aktive monatliche Zählerpläne erzeugen genau eine automatisch verwaltete
  Aufgabe pro Zähler und Monat. Eine gespeicherte Ablesung erledigt die Aufgabe;
  deaktivierte Pläne erzeugen keine neue Aufgabe.
- Das Dashboard unterscheidet **PV-Erzeugung** und **PV eingespeist**. Beide
  Kacheln erscheinen nur, wenn ein passender dashboardrelevanter Zähler vorhanden
  ist; mehrere ausgewählte PV-Zähler werden gemeinsam ausgewertet.
- Die elektrische Topologie liefert neben den gespeicherten auch die wirksamen
  Phasen. Alte Widersprüche bleiben sichtbar und erhalten eine Warnung, während
  neue Verbindungen an einphasigen Schutzgeräten nur die berechnete Phase
  akzeptieren.
- Haupt-/Unterverteilungen werden als strukturelle Behälter behandelt. Neue
  Verkabelungen werden an enthaltenen Einbaugeräten und Klemmen dokumentiert.
- Der Aufbau **Verteilerdose** steht für Verbindungsklemmen ohne sichtbares
  Reihen- oder TE-Raster zur Verfügung.
- Kamm-/Phasenschienen werden als Overlay über beziehungsweise unter
  Schutzgeräten dargestellt, belegen selbst keine TE und können nicht archiviert
  werden, solange sie noch Schutzgeräte überdecken.
- Repository-, Release- und Support-Verweise sind fest im Quellstand und in
  `SOURCE_INFO.json` enthalten; sie bleiben deshalb auch außerhalb einer
  `.git`-Arbeitskopie erhalten.
- Der Duplizier-/Seriendialog bietet für die fortlaufende DIN-Platzierung nur
  Verteilungen mit Reihen- oder Bereichslayout an. Verteilerdosen werden dort
  ausgeschlossen, wodurch der TypeScript-Fehler beim Docker-Frontend-Build
  behoben ist.
- Kamm-/Phasenschienen werden bei der Platzierungsprüfung nun konsequent als
  Anschlusskomponenten ohne eigene TE-Belegung behandelt. Sie dürfen bestehende
  Schutzgeräte und normale DIN-Assets überspannen. Eine Überschneidung wird nur
  noch zwischen Schienen auf derselben Montageebene oberhalb beziehungsweise
  unterhalb blockiert.
- Liegt ein Schutzgerät unter einer Sammel-/Phasenschiene, wird seine wirksame
  Außenleiterphase im Verkabelungsdialog automatisch aus Position und Startphase
  der Schiene übernommen. L1/L2/L3 können dort nicht mehr manuell abweichend
  gewählt werden; N und PE bleiben auswählbar. Das Backend erzwingt dieselbe
  Zuordnung auch für direkte API-Aufrufe und korrigiert eine alte Abweichung beim
  nächsten Speichern der Verbindung.
- Validierungsfehler beim Bearbeiten von Schrankkomponenten und elektrischen
  Verbindungen erscheinen innerhalb des geöffneten Dialogs statt verdeckt im
  Seitenhintergrund.

## Datenbank

Alembic-Migration `0039`:

- ergänzt den eindeutigen Automationsschlüssel für erzeugte Ableseaufgaben;
- ergänzt die Montageposition `above`/`below` für Kamm-/Phasenschienen;
- erlaubt den Verteilungsaufbau `junction_box`.

Die Migration ersetzt keine vorhandenen Zählerstände, Assets, Bilder,
Dokumente oder Verkabelungen. Vor dem Update ist trotzdem ein vollständiges
Backup des persistenten `data`-Ordners erforderlich.

## Update von 1.6.1

1. In DocOfHome ein Backup erstellen und den persistenten `data`-Ordner extern sichern.
2. Container stoppen: `docker compose down`.
3. Version 1.6.2 in einen neuen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. `docker compose build --no-cache` und `docker compose up -d` ausführen.
6. Prüfen, dass Migration `0039` erfolgreich ausgeführt wurde.
7. Aufgaben, Zähler-Dashboard, Topologie und Verteilerdosen praktisch prüfen.
