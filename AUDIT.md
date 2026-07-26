# DocOfHome – aktueller Audit- und Qualitätsstatus

Stand: 25. Juli 2026
Release: 1.4.2
Alembic-Head: `0036`

## Einordnung

1.4.2 entfernt installationsabhängige Projekt- und Impressumsangaben und
verlagert spätere GitHub-Verweise in eine zentrale Quellcodedatei. Feedback ist
direkt aktiv und wird als begrenztes ZIP an einen festen öffentlichen Nextcloud
File Drop übertragen.

## Wesentliche Integritätsregeln

- Das Feedback-ZIP enthält nur Text, strukturierte Basisdaten und optional
  ausdrücklich freigegebene technische Angaben.
- Datenbank, Integrationskonfiguration, Passwörter und Tokens werden nicht
  aufgenommen.
- Uploadziel und spätere Projektlinks sind nicht über die Oberfläche änderbar.
- Das serverseitige Rate-Limit und die maximale ZIP-Größe bleiben aktiv.
- Migration `0036` entfernt nur die obsoleten About-/Impressumsfelder.
- Die Elektro-, Verbrauchs-, Asset- und Integrationsmodelle bleiben unverändert.

## Qualitätsnachweis

Die tatsächlich ausgeführten Prüfungen und verbleibenden Zielsystemprüfungen
stehen in `docs/VALIDATION_REPORT_1.4.2.md`. Das Releasemanifest enthält Pfad,
Dateigröße und SHA-256 für jede ausgelieferte Datei.
