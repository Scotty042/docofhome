# DocOfHome – Projektstatus

Stand: 5. Oktober 2026  
Release: **1.7.20**  
Alembic-Head: **`0059`**

DocOfHome ist als selbst gehostete Hausdokumentation mit den Bereichen Assets, Elektro, Netzwerk, Verbrauch, Wartung, Kochbuch, Bilder, Dokumente und Dienste/Container aufgebaut. Die Module sind separat aktivierbar und können unabhängig im Hauptmenü ein- oder ausgeblendet werden.

## Aktueller technischer Stand

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
