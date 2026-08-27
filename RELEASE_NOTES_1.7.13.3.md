# DocOfHome 1.7.13.3

Korrektur und Ausbau der Rezeptbilder sowie der Zutatenanzeige.

- Rezeptbilder werden im normalen Editor nicht mehr über ein URL-Feld gepflegt.
- Neue Aktionen **Foto aufnehmen**, **Bild auswählen** und **Aus Immich auswählen**.
- Aufgenommene und ausgewählte Dateien werden optimiert als WebP lokal unter dem persistenten DocOfHome-Datenverzeichnis gespeichert.
- Aus Immich gewählte Bilder werden beim Übernehmen nach DocOfHome kopiert; das Rezept bleibt damit unabhängig von einer späteren Immich-Verfügbarkeit.
- Eine manuelle Bild-URL bleibt nur noch unter **Erweitert** als Sonderfall verfügbar.
- Lokale Rezeptbild-Pfade werden von der Rezept-API ausdrücklich unterstützt.
- In der Rezeptdetail- und Druckansicht gibt es nun zuverlässig Abstand zwischen Mengenangabe/Einheit und Zutatenname, z. B. `130 g Salatgurke`.
- Keine Datenbankmigration; Alembic-Head bleibt `0052`.
