# DocOfHome 1.5.0 – Handbuch & Glossar

Stand: 26. Juli 2026  
Alembic-Head: `0036`

## Neu

- statische, vollständig offline nutzbare Seite **Wiki → Handbuch & Glossar**;
- 109 verständlich erklärte Begriffe aus Einstieg, Assets, Elektro, Netzwerk,
  Verbrauch, Home Assistant, Bildern/Dokumenten sowie Backup/Betrieb;
- zentrale Frontend-Datenstruktur ohne neue Datenbanktabelle oder Migration;
- Suche über Begriff, Alias, Beschreibung, Beispiel, Kategorie und verwandte
  Begriffe;
- Kategorienfilter und alphabetisches Glossar mit A–Z-Sprungmarken;
- einklappbare Handbuchabschnitte, Inhaltsverzeichnis und interne Ankerlinks;
- responsive Darstellung mit mobilem Inhaltsverzeichnis und großen Touch-Zielen;
- verbindlicher Hinweis, dass Änderungen an elektrischen Anlagen in die Hände
  einer Elektrofachkraft gehören.

## Elektro-Detailansicht

- platzierte Schutzgeräte und andere DIN-Assets besitzen nun den gut sichtbaren
  Button **Asset bearbeiten**;
- **Position bearbeiten** beziehungsweise **Position / Gruppe** bleibt erhalten;
- reine passive Schrankkomponenten zeigen weiterhin keinen Asset-Button;
- die normale Asset-Bearbeitungsseite wird verwendet, damit keine zweite
  Bearbeitungslogik entsteht.

## Kompatibilität und Daten

- keine neue Datenbankmigration; Alembic-Head bleibt `0036`;
- bestehende Wiki-Seiten bleiben editierbar und unverändert unter `/wiki`;
- das Handbuch liegt unter `/wiki/handbuch` und benötigt weder API noch Internet;
- bestehende Assets, Produkte, Verteilungen, Zähler, Netzwerkdaten,
  Home-Assistant-Zuordnungen, Verkabelungen und Bilder bleiben unverändert.

## Prüfung

Der tatsächliche Prüfstatus ist im Release-Artefakt
`DocOfHome-1.5.0-VALIDATION.md` und in
`docs/VALIDATION_REPORT_1.5.0.md` dokumentiert. Nicht ausgeführte oder durch die
Arbeitsumgebung blockierte Prüfungen werden dort ausdrücklich als offen
gekennzeichnet.
