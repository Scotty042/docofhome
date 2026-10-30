# DocOfHome – Projektstatus

Stand: 30. Oktober 2026  
Release: **1.9.3**  
Alembic-Head: **`0061`**

DocOfHome ist als selbst gehostete Hausdokumentation mit den Bereichen Assets, Elektro, Netzwerk, Verbrauch, Wartung, Kochbuch, Bilder, Dokumente und Dienste/Container aufgebaut. Die Module sind separat aktivierbar. Aktivierte Module bleiben in der gruppierten Navigation erreichbar; die Hauptmenü-Auswahl steuert den Schnellzugriff.

## Aktueller technischer Stand

- AMS-Karten mit Lagerrollendetails; gemeinsamer Abruf eindeutig passender Bambu-Originalbilder für Rollen ohne Bild;

- kompakte Darstellung mit kleineren Titeln, kürzeren Tabellenzeilen und reduzierten Abständen;
- responsives Salbei-Design mit neuer Navigation, Dashboard, Inventarliste und gegliederten Gerätedetails;

- Filament-Sammlung für beliebige Hersteller mit optionaler direkter Bambu-Cloud-/AMS-Anbindung, lokalem Archiv, Nachkaufliste, Bildern und 40 × 30 mm QR-Etiketten;
- insgesamt 49 MCP-Werkzeuge, davon acht für Filament; Lese-, Schreib- und Vollzugriff weiterhin getrennt;

- optionale tägliche Push-Erinnerungen über Pushover und ntfy mit Testversand, Kategorien und dauerhaftem Versandstatus;

- LEGO-Sammlung mit Bilddashboard, Kaufkosten/Teilezahlen, manueller Bearbeitung, Modellmaßen und fünf MCP-Werkzeugen;

- zentrale Versions- und Implementierungshistorie in `PROJECT_HISTORY.md`;
- FastAPI/SQLModel/Alembic-Backend und Vue/Vuetify-Frontend;
- FRITZ!Box-Abgleich über normalisierte MAC-Adressen;
- Docker-Engine-Synchronisierung für Container auf einem konfigurierten Host-Asset;
- optionale Integrationen für Home Assistant, Immich, Nextcloud und Paperless-ngx;
- Bezugsobjekt-Profile und objektübergreifender Lebenslauf für Wartungen, Prüfungen, Messungen und Termine;
- manuelle Paperless-Verknüpfungen an Wartungs-/Historieneinträgen ohne PDF-Duplikate;
- MCP-Endpunkt für berechtigten Lese-/Schreibzugriff;
- mehrere Docker-Hosts per fest gepinnter SSH-Public-Key-Verbindung oder lokalem Socket;
- persistente Daten unter `/data` und migrationsgestützte Updates.

Vor jedem Update ist ein vollständiges Backup des persistenten `data`-Ordners empfohlen. Release-spezifische Details und frühere technische Entscheidungen stehen ausschließlich in `PROJECT_HISTORY.md`.
