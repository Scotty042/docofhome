# Monatliche CSV-Exporte der Zeiterfassung

Ab Version 1.11.0 unter **Zeiterfassung → Monatlicher CSV-Export** verfügbar. Die Automatik ist zunächst ausgeschaltet.

## Einrichtung und Bedienung

1. Den Bereich unter dem Verlauf aufklappen.
2. **Monatlichen CSV-Export aktivieren** setzen.
3. Optional **CSV zusätzlich nach Nextcloud hochladen** wählen und einen relativen Zielordner angeben, z. B. `DocOfHome/Zeiterfassung`. Dafür wird die vorhandene Nextcloud-Integration verwendet; es werden keine weiteren Zugangsdaten gespeichert.
4. **Einstellungen speichern** drücken.

Lokal wird immer eine CSV erzeugt. Sie kann direkt in diesem Bereich heruntergeladen werden. Fehler beim Nextcloud-Upload werden angezeigt; die lokale Datei bleibt erhalten. Schreibrechte im Zielordner müssen zusätzlich zu Leserechten vorhanden sein.

**Vormonat jetzt exportieren** erzeugt die CSV des zuletzt abgeschlossenen Monats erneut, auch bei ausgeschalteter Automatik. Es verwendet die gespeicherten Upload-Einstellungen und ersetzt für diesen Monat die bisherige Datei; ein aktivierter Nextcloud-Upload aktualisiert dieselbe entfernte Datei. Nach späteren Zeit-/BCS-Korrekturen im Vormonat lässt sich so ein neuer Stand erzeugen. Änderungen an den Einstellungen vorher speichern.

## Monatsgrenzen und Automatik

Die eingestellte **DocOfHome-Installationszeitzone** bestimmt die Monatsgrenzen, nicht die Uhrzeit des Browsers. Der Hintergrunddienst prüft beim Start und danach stündlich, ob ein abgeschlossener Monat fehlt. Es ist kein separater Cron-Container nötig.

Bei erstmaliger Aktivierung beginnt die Automatik mit dem dann abgeschlossenen Vormonat, nicht mit der gesamten vorhandenen Historie. Danach werden nach Ausfallzeiten fehlende Monate nachgeholt, höchstens zwölf pro Prüflauf. Ein Monat wird erst als abgeschlossen markiert, wenn die lokale Datei und gegebenenfalls der Nextcloud-Upload erfolgreich sind. Bei einem erneuten Versuch wird die bereits erstellte lokale Datei verwendet. Fertige automatische Monatssnapshots werden nicht bei jeder nachträglichen Zeitänderung überschrieben.

Während der Container ausgeschaltet ist, kann kein Export laufen; das Nachholen geschieht nach dem Start. Nach dem Ausschalten der Automatik bleiben vorhandene CSVs erhalten. Es gibt keine automatische Löschung alter Exportdateien.

## Inhalt und Format

Dateiname: `docofhome-zeiten-YYYY-MM.csv`. UTF-8 mit BOM, Semikolon als Trennzeichen, ein Arbeitslauf beziehungsweise Monatsanteil pro Zeile. Leere Monate erhalten eine Datei mit Kopfzeile.

Spalten: Arbeitslauf-ID, Tätigkeit/Ticketnr, Kunde, weitere Info, Anfang, Ende, Dauer in Sekunden, Dauer als HH:MM:SS, BCS (1/0) und Status.

Anfang und Ende sind ISO-8601-Zeiten mit lokalem UTC-Offset; Sommer-/Winterzeit bleibt nachvollziehbar. Arbeitsläufe über Monatsgrenzen werden auf den Anteil des exportierten Monats begrenzt. Ein noch laufender Arbeitslauf kann mit seinem abgeschlossenen Monatsanteil enthalten sein; er wird dadurch nicht beendet. Die Originalzeiten in DocOfHome ändern sich nicht. Parallele Tätigkeiten werden weiterhin einzeln summiert.

Benutzertexte werden mit CSV-Quoting geschrieben. Gängige Tabellenkalkulations-Formelpräfixe in Tätigkeit, Kunde und Info werden mit einem führenden Apostroph als Text geschützt. Dieser Zusatz betrifft die Exportdarstellung, nicht die gespeicherten Originaldaten.

## Speicherung, Backup und Wiederherstellung

Dateien und Einstellungen liegen unter `/data/exports/time-tracking/`. Die Konfiguration mit aktiviertem Zustand, Monatsfortschritt und letztem Ergebnis wird atomar gespeichert und bleibt nach Neustarts erhalten. Vollständige Backups enthalten Konfiguration und CSV-Dateien mit Prüfsummen. Allgemeine JSON-/CSV-Datenimporte von Arbeitsläufen bleiben weiterhin gesperrt.

Beim Wiederherstellen eines älteren Backups **ohne** Exportkonfiguration wird eine später eingerichtete Exportautomatik deaktiviert; die bisherige Konfiguration wird im Pre-Restore-Sicherungsordner aufgehoben. So wird nicht unbeabsichtigt ein späterer Upload-Job auf einen älteren Datenbestand angewendet. Bereits vorhandene CSVs werden dabei nicht gelöscht. Beim Wiederherstellen eines neuen Backups wird dessen enthaltene Exportkonfiguration wiederhergestellt. Backups mit diesen zusätzlichen Dateien benötigen für die Wiederherstellung Version 1.11.0 oder neuer; ältere Backups bleiben lesbar.

## MCP und Zugriff von außen

- `get_time_exports`: Konfiguration/Status und Dateiliste, read.
- `configure_time_exports`: Automatik und optionalen Nextcloud-Upload konfigurieren, write.
- `run_time_export`: Vormonat erneut erzeugen und gegebenenfalls hochladen, write.

Insgesamt 59 MCP-Werkzeuge; Werkzeugliste nach Update neu laden. Browser-Downloads erfolgen über die geschützte Oberfläche. Die separate MCP-SWAG-Vorlage veröffentlicht keine allgemeinen Download- oder App-API-Routen. Authentik wird für den Container-internen Exportdienst nicht benötigt; externe Downloads müssen dagegen über die vorgesehene Anmeldung geschützt werden.
