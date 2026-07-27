# Migration auf DocOfHome 1.6.0

1. Lokales DocOfHome-Backup erzeugen.
2. Persistenten `data`-Ordner zusätzlich extern sichern.
3. Container stoppen.
4. Release 1.6.0 in einen sauberen Ordner entpacken.
5. Lokale `.env`- und Compose-Anpassungen übernehmen.
6. Image ohne Cache bauen und Container starten.
7. Logs und Healthcheck prüfen.
8. Kontrollieren, dass Alembic-Head `0037` erreicht wurde.

Migration 0037 ergänzt ausschließlich optionale Felder für Sicherungsautomaten
und Stromstoßschalter sowie neue Tabellen für Smart-Meter-Messpunkte. Bestehende Backup-Archive mit dem Präfix
`tectoryn-backup-` werden weiterhin akzeptiert.

Nach dem Update praktisch prüfen:

- Assistenten-Schrittwechsel und Abschluss;
- neues Backup und Restore-Validierung;
- Schrankansicht auf PC oder Tablet;
- vorhandene Wasser-/Gaszähler in der Verbrauchsverwaltung;
- Sicherungsautomat-Stammdaten;
- Smart-Meter-Messpunkt an einer bestehenden Verkabelung.
