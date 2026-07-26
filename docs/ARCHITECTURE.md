# DocOfHome 1.1 – Architektur

DocOfHome ist eine lokale Single-Installation mit FastAPI, SQLModel, SQLite,
Alembic und einer Vue-3-SPA. Der Browser spricht ausschließlich mit der lokalen
API. Persistente Daten liegen unter dem konfigurierten Datenverzeichnis; externe
Systeme bleiben Eigentümer ihrer Inhalte.

## Zentrale Bausteine

- `DashboardSetting` hält Reihenfolge und Sichtbarkeit der Kacheln. Kritische
  Hinweise werden unabhängig von dieser Konfiguration berechnet.
- Verbrauchszähler definieren optional einen Primärzähler je Medium sowie einen
  monatlichen, zeitzonensicheren Ableseplan.
- `EnergyConfiguration` referenziert die bestehenden kWh-Zähler für Netzbezug,
  PV-Erzeugung und Netzeinspeisung und speichert Anschlussstammdaten.
- `EnergyComponent` dokumentiert beliebig viele PV-Quellen, Wechselrichter und
  Speicher und kann auf ein vorhandenes Asset zeigen.
- Die Energiebilanz wird bei der Abfrage aus periodenbezogenen Zählerdifferenzen
  berechnet; abgeleitete Monatswerte werden nicht gespeichert.
- Die Elektroversorgung ist ein gerichteter azyklischer Graph. Mehrere Quellen
  je Ziel sind zulässig, Zyklen und identische Doppelverbindungen nicht.
- Wartungen unterscheiden Intervallregeln relativ zur Erledigung von festen
  Kalenderregeln. Ableseerinnerungen werden zusätzlich in diesem Modul gezeigt.
- `ServiceWorkload` modelliert logische Dienste unter einem physischen Host-Asset.
- `AuditEvent` wird beim ORM-Flush erzeugt, redigiert sensible Felder und ist
  unveränderlich.
- `GuidedSetupDraft` speichert den Fachassistenten; der Apply-Service erzeugt die
  gewählte Objektkette in einer Datenbanktransaktion.

## Datenflüsse und Sicherheitsgrenzen

```text
Vue SPA -> lokale FastAPI -> SQLite
                       |-> Home Assistant (read-only)
                       |-> Immich (read-only)
                       |-> Nextcloud WebDAV (nur explizite Dokument-/Backupaktionen)
                       `-> FRITZ!Box TR-064 (read-only)
```

Connectoren besitzen Zeit- und Größenlimits. Secrets werden weder an den Browser
noch an Export oder Audit-Historie ausgegeben. Die visuelle Immich-Auswahl
verwendet ausschließlich den serverseitigen Thumbnail-Proxy.

## Migration und Kompatibilität

Die Migrationen 0024–0027 bauen additiv auf 0023 auf. Migration 0027 ergänzt den
Einspeisezählertyp, Energieobjekte und die Mehrquellenfähigkeit. Technische
Altverträge wie `jarvis_code`, Umgebungsvariablen mit Präfix `JARVIS_` und der
bestehende SQLite-Dateiname bleiben updatekompatibel; sie sind keine sichtbare
Produktbezeichnung.
