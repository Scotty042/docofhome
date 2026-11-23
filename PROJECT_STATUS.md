# DocOfHome – Projektstatus

Stand: 23. November 2026  
Release: **1.11.2**  
Alembic-Head: **`0063`**

DocOfHome ist als selbst gehostete Hausdokumentation mit den Bereichen Assets, Elektro, Netzwerk, Verbrauch, Wartung, Kochbuch, Bilder, Dokumente und Dienste/Container aufgebaut. Die Module sind separat aktivierbar. Aktivierte Module bleiben in der gruppierten Navigation erreichbar; die Hauptmenü-Auswahl steuert den Schnellzugriff.

## Aktueller technischer Stand

- Monatlicher CSV-Export mit eigenem Schalter, lokal und optional Nextcloud; Status, Downloads, Wiederholung und Backup/Wiederherstellung der Exporte.
- Gruppierung nach Kunde als Checkbox, gemeinsame Tabellenüberschriften einmal je Tag.
- Optionale separate Compose-/SWAG-/Authentik-Vorlagen vorbereitet; keine automatische Freigabe und kein Authentik-Dienst installiert.

- Zeiterfassung mit Sortierung innerhalb der Tagesgruppen, optionaler Kundengruppierung mit Kundensummen, Kundenname in den Tätigkeitssummen und gespeicherter BCS-Markierung. Migration `0063`.

- Nach erfolgreich gespeichertem Ende werden die drei Eingabefelder für die nächste Tätigkeit geleert. Pause und fehlgeschlagenes Speichern erhalten die Eingaben.

- Parallele Tätigkeiten können bei manuellen Arbeitsläufen und nachträglichen Zeitänderungen überlappen. Tätigkeitsdauern werden einzeln summiert.

- Arbeitsläufe über Löschen mit Bestätigungsdialog entfernen; laufende Timer geschützt, Summen und Wiederaufnahme aktualisiert. MCP-Löschen erfordert admin.

- Zeiterfassungsverlauf mit Datumsüberschriften und Tagessummen; Tätigkeit/Ticketnr und Kunde nebeneinander; Wiederaufnahme nur für Tätigkeiten mit Arbeitszeit heute.

- Verlauf der Zeiterfassung mit Standard letzte 30 Tage, Schnellauswahl und Von/Bis; manuelle Arbeitsläufe und nachträgliche Änderungen mit erlaubten Überschneidungen.

- Ticketbasierte Zeiterfassung mit einzelnen Arbeitsläufen, Start/Pause/Ende, Wiederaufnahme, Ticket- und Tagessummen; zehn MCP-Werkzeuge und Datenexport. Migration `0062`.

- AMS-Karten mit Lagerrollendetails; gemeinsamer Abruf eindeutig passender Bambu-Originalbilder für Rollen ohne Bild;

- kompakte Darstellung mit kleineren Titeln, kürzeren Tabellenzeilen und reduzierten Abständen;
- responsives Salbei-Design mit neuer Navigation, Dashboard, Inventarliste und gegliederten Gerätedetails;

- Filament-Sammlung für beliebige Hersteller mit optionaler direkter Bambu-Cloud-/AMS-Anbindung, lokalem Archiv, Nachkaufliste, Bildern und 40 × 30 mm QR-Etiketten;
- insgesamt 59 MCP-Werkzeuge, davon acht für Filament; Lese-, Schreib- und Vollzugriff weiterhin getrennt;

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
