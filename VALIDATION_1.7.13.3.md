# Validierung DocOfHome 1.7.13.3

- Rezepteditor auf Kamera-, lokale Datei- und Immich-Auswahl umgestellt.
- Normales Bild-URL-Feld aus dem Hauptformular entfernt; manuelle URL nur noch unter „Erweitert“.
- Persistente lokale Speicherung für Rezeptbilder mit JPEG/PNG/WebP-Eingabe, Größenlimit und WebP-Optimierung ergänzt.
- Immich-Auswahl kopiert das gewählte Vorschaubild in den lokalen Rezeptbildspeicher.
- Rezept-Schema akzeptiert HTTP(S)-URLs sowie lokale Pfade beginnend mit `/`.
- Zutatenabstand in Detailansicht und Druckansicht explizit per Abstandsklasse abgesichert.
- Neue Frontend-Vertragstests und Backend-Tests für die Rezeptbild-Pfade ergänzt.
- Keine Datenbankmigration erforderlich; Alembic-Head bleibt `0052`.

## Ausgeführte Prüfungen

- Python-Syntaxprüfung für Backend und Tests: erfolgreich.
- DocOfHome-Versionskonsistenz: erfolgreich.
- Releasevertrag 1.7.13.3: erfolgreich.
- Branding, gesammelte Fix-Verträge, Ableseerinnerungen und Migration 0052 statisch geprüft: erfolgreich.
- 195 TypeScript-/Vue-Skripteinheiten syntaktisch geprüft: erfolgreich.
- Lokaler Rezeptbildspeicher mit erzeugtem JPEG → WebP und anschließendem Resolve praktisch geprüft: erfolgreich.

## In dieser Umgebung nicht vollständig ausführbar

- Vollständiger Backend-Pytest-Lauf nicht möglich, da `sqlmodel` in der isolierten Laufzeit nicht installiert ist.
- Vollständiger Frontend-Vitest-/Vue-Typecheck-/Vite-Build nicht möglich, da `frontend/node_modules` nicht im Quellpaket enthalten ist und externe Paketdownloads in dieser Umgebung nicht zur Verfügung stehen.
