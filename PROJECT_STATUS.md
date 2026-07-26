# DocOfHome – Projektstatus

Stand: 26. Juli 2026  
Release: 1.5.0  
Alembic-Head: `0036`

DocOfHome 1.5.0 ergänzt die private Hausdokumentation um ein statisches,
offline nutzbares Handbuch und Glossar. Die bestehende editierbare Wiki-Funktion
bleibt unverändert erhalten.

## Aktueller Funktionsstand

Zusätzlich zum Funktionsumfang aus 1.4.2:

- Navigation **Wiki → Handbuch & Glossar**;
- eigene Route `/wiki/handbuch` mit internen Ankerlinks;
- 109 zentrale Begriffe in acht verständlichen Themenbereichen;
- Suche, Kategorienfilter, alphabetisches Glossar und A–Z-Sprungmarken;
- Desktop-Inhaltsverzeichnis und mobile einklappbare Navigation;
- verständliche Beispiele aus typischen Privathaushalten;
- Elektro-Sicherheitshinweis ohne Anspruch auf Planung oder Beratung;
- Button **Asset bearbeiten** in der Detailansicht assetgebundener DIN-Geräte;
- kein Asset-Button bei passiven Schrankkomponenten.

## Daten- und Updatezustand

Für 1.5.0 ist keine neue Migration erforderlich. Alembic-Head bleibt `0036`.
Handbuch und Glossar werden als statische Frontend-Inhalte ausgeliefert. Alle
bestehenden Fachdaten und Integrationszuordnungen bleiben unverändert.

Vor jedem Update ist weiterhin ein vollständiges Backup des persistenten
`data`-Ordners erforderlich.

Einzelheiten stehen in `RELEASE_NOTES_1.5.0.md`,
`docs/VALIDATION_REPORT_1.5.0.md` und
`docs/KNOWN_LIMITATIONS_1.5.0.md`.
