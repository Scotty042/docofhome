# LEGO-Sammlung ab 1.7.20

Unter **LEGO-Sammlung → Set erfassen** Setnummer und Name eingeben. Alle weiteren Angaben sind optional. Nummern mit Standardvariante `-1` werden normalisiert: `10305` und `10305-1` sind dasselbe Set. Doppelte Nummern können nicht gespeichert werden. Einzelne Steine werden nicht inventarisiert.

Die Bildübersicht zeigt dein Setfoto, Namen, Themenwelt, Status, Lagerort, Kaufpreis, Teilezahl und Maße. Klicken öffnet Details. Bearbeiten erlaubt Änderungen aller Angaben. Bilder können per URL, Upload, Immich oder über die vorhandene Produktbildsuche eingetragen werden. Die Produktbildsuche ist keine Setdaten-Recherche.

## Kennzahlen und Filter

- Sets: Anzahl aller gespeicherten Sets.
- Kaufkosten: Summe tatsächlich erfasster Kaufpreise in **EUR**, kein Sammlerwert. Fehlende Preise bleiben leer; ein Geschenk kann 0 EUR kosten.
- Teilezahl: Summe hinterlegter Teilezahlen, keine Bestandsprüfung der einzelnen Teile. Fehlende Teilezahlen bleiben leer.

Fehlende Angaben werden unter den Kennzahlen gezählt. Suche und Filter ändern die angezeigten Karten, die Kennzahlen bleiben Gesamtwerte. Nach externem Eintragen über MCP mit Aktualisieren neu laden.

## Lagerung und Modellmaße

Bestehenden Lagerort auswählen; Box, Regal oder getrennte Aufbewahrung von Karton/Anleitung in Lagerung beziehungsweise Notizen ergänzen. Breite, Tiefe und Höhe beziehen sich auf das **aufgebaute Modell**, in Zentimetern. Verpackungsmaße nicht verwenden. Bei mehreren Modellen, geöffneten Türen oder ausgeklappten Flügeln den Zustand im Maßhinweis nennen. Unbekannte Maße leer lassen. Quellen-URL und Recherchedatum dokumentieren.

## Online-Recherche und MCP

Der Assistent recherchiert Angaben online und kann sie danach über die vorhandene MCP-Verbindung speichern. DocOfHome benötigt keinen externen Katalogschlüssel und ruft selbst keinen Setkatalog ab. Die Verfügbarkeit von Bildern und Maßen hängt von der Quelle ab. Manuell eingegebene Daten bleiben jederzeit änderbar.

1. `search_lego_sets(set_number="10305")`: exakte Dublettenprüfung. Suche mit `query`, `offset` und `limit` möglich; bei `has_more` mit `next_offset` fortsetzen.
2. Online recherchieren. Verlässliche Quelle, Bild-URL, Teilezahl und gegebenenfalls Modellmaße ermitteln; fehlende Werte nicht schätzen.
3. `save_lego_set(data={"set_number":"10305","name":"…","parts_count":4514,"source_url":"https://…","researched_at":"2026-10-05"})`: neues Set.
4. `get_lego_set(set_id="…")`: vollständigen Datensatz lesen. `save_lego_set(set_id="…",data={"storage_note":"Box 3"})` ändert nur angegebene Felder. Andere Daten bleiben erhalten; `null` entfernt optionale Angaben. Vor Änderungen vorhandener Daten die Absicht des Nutzers beachten.
5. `get_lego_dashboard()`: Kennzahlen. `delete_lego_set(set_id="…")`: löschen.

Lesen benötigt `read`, Speichern `write`, Löschen `admin`. Insgesamt sind 41 Werkzeuge registriert. Bearer-Authentifizierung und `/mcp/<token>` bleiben verfügbar.

## Menü, Sicherung und Änderungen

Unter **Einstellungen → Module** LEGO im Hauptmenü aus-/einblenden oder als Modul deaktivieren. Ausblenden löscht keine Daten. Das statische Handbuch bleibt als Anleitung verfügbar.

Ungespeicherte Editoränderungen werden beim Schließen, bei Navigation und beim Neuladen/Verlassen des Browsers abgefragt. Speichern/Verwerfen bleibt am unteren Rand des Editors erreichbar.

Die Datenbank ist Teil des vollständigen Backups; lokale Setbilder unter `uploads/` werden ebenfalls gesichert. JSON- und CSV-Export/Import enthalten die Setdaten und Bildverweise, nicht die Bilddateien. Für Übertragung lokaler Bilder daher vollständiges Backup verwenden. Importstrategie `skip` überspringt bestehende Setnummern; `fail` bricht bei Konflikten ab.
