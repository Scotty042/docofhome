# Sprint 0009 – Backup und Wiederherstellung

## Ziel

Tectoryn muss seine vollständige SQLite-Datenbank ohne manuelle Dateiarbeit sichern und nach einer Prüfung kontrolliert wiederherstellen können. Lokale Backups sind immer verfügbar; ein zusätzlicher Upload in die konfigurierte Nextcloud ist optional.

## Umsetzung

- Konsistenter Snapshot über die SQLite-Backup-API statt Kopieren einer geöffneten Datenbankdatei.
- ZIP-Archiv mit `database.sqlite3` und `manifest.json`.
- SHA-256-Prüfsumme der Datenbank im Manifest und des gesamten Archivs in der API-Antwort.
- SQLite-`PRAGMA integrity_check` bei Erstellung, Validierung und unmittelbar vor einer Wiederherstellung.
- Persistente Ablage unter `/data/backups`.
- Optionaler WebDAV-Upload mit der bereits gespeicherten Nextcloud-Integration.
- Automatisches Anlegen des konfigurierten Nextcloud-Zielpfads über `MKCOL`.
- Automatische Backups mit Intervall, Aufbewahrungszahl, optionalem Nextcloud-Upload und Status des letzten Laufs.
- Stündliche Fälligkeitsprüfung im laufenden Container.
- Separate Konfiguration unter `/data/backups/config.json`; sie wird nicht durch eine Datenbankwiederherstellung zurückgesetzt.
- Wiederherstellung wird nur vorgemerkt. Die Datenbank wird vor dem Anwendungsstart und vor Alembic-Migrationen ausgetauscht.
- Vor jedem Austausch wird die bisherige Datenbank zusätzlich nach `/data/backups/pre-restore` kopiert.
- Explizite Bestätigung mit `WIEDERHERSTELLEN`.

## Sicherheitsgrenzen

- Kein Austausch der SQLite-Datei bei laufenden Datenbankverbindungen.
- Keine Annahme beliebiger ZIP-Inhalte; exakt Datenbank und Manifest sind erlaubt.
- Backup-Dateinamen werden auf Traversal geprüft.
- Nextcloud-Zielsegmente `.` und `..` werden abgelehnt.
- WebDAV-Weiterleitungen werden nicht verfolgt.
- Zugangsdaten verbleiben im Backend und werden nicht an den Browser zurückgegeben.
- Pre-Restore-Sicherheitskopien werden nicht automatisch durch die normale Aufbewahrungsregel gelöscht.

## Bedienung

Der feste Navigationspunkt **Backup** bietet:

1. Manuelles lokales Backup.
2. Optionalen gleichzeitigen Nextcloud-Upload.
3. Automatische Sicherung mit Intervall und Aufbewahrungszahl.
4. Liste lokaler Sicherungen mit Datum, Größe, Version und SHA-256.
5. Manuelle Integritätsprüfung.
6. Vorgemerkte Wiederherstellung beim nächsten Containerstart.

## Betriebshinweis

Nach dem Vormerken einer Wiederherstellung muss der Container kontrolliert neu gestartet werden. Beim Start wird zuerst die vorgemerkte Datenbank eingesetzt, danach werden vorhandene Alembic-Migrationen bis zum aktuellen Stand ausgeführt.
