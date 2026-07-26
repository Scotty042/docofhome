# DocOfHome 1.4.1

DocOfHome 1.4.1 ergänzt die vorbereitete Info-Seite und vereinfacht die mobile
Zählerstandserfassung direkt vom Dashboard.

## Info-Seite

Unter **Mehr → Über DocOfHome** stehen nun vier klar getrennte Bereiche zur
Verfügung:

- **Projekt** mit Zweck, lokaler Datenhaltung und optionalen Projektverweisen;
- **Versionen & Changelog** aus den mitgelieferten Release Notes;
- **Feedback** als optional aktivierbares Formular;
- **Impressum**, sobald mindestens ein konfiguriertes Feld vorhanden ist.

Die installierte Version wird aus derselben zentralen Versionsquelle wie das
Backend gelesen. Release Notes werden serverseitig geladen und im Frontend ohne
ausführbares HTML dargestellt.

## Konfiguration

In den Einstellungen können optional gepflegt werden:

- Projektwebseite, Repository-, Release- und Fehler-/Feedback-URL;
- Lizenzhinweis;
- Betreiber, Anschrift, Kontakt, verantwortliche Person, Register- und
  Umsatzsteuerangaben sowie freier Impressumstext;
- Aktivierung des Feedbackformulars und ein fester Nextcloud-Zielordner.

Leere Angaben erscheinen nicht auf der Info-Seite. Das Standard-Release enthält
keine persönlichen Impressumsdaten.

## Feedback über Nextcloud

Feedback ist standardmäßig deaktiviert. Nach Aktivierung wird es ausschließlich
über das Backend und die vorhandene Nextcloud-Integration als UTF-8-Markdown-Datei
hochgeladen. Der Browser erhält keine WebDAV-Zugangsdaten.

Technische Angaben werden nur nach sichtbarer Zustimmung übertragen. Angezeigt
und übertragen werden dann ausschließlich App-Version, betroffene Route,
Browserkennung und Fenstergröße. Dateinamen werden serverseitig aus Zeitstempel
und Zufallsanteil erzeugt. Größenlimits, feste Kategorien und ein einfaches
Rate-Limit begrenzen die Übertragung.

## Dashboard und mobile Ablesung

- Die bisherige Versionskachel wurde vom Dashboard entfernt.
- Ein gut sichtbarer Button **Zählerstände erfassen** öffnet direkt den
  Ablesedialog.
- Auf kleinen Bildschirmen nimmt der Button die volle Breite ein.
- Bestehende gespeicherte Dashboard-Layouts werden automatisch von der alten
  Systemkachel bereinigt.

## Migration

Alembic `0035_about_page_and_feedback` ergänzt ausschließlich optionale
Konfigurationsfelder. Bestehende Gebäude-, Asset-, Elektro-, Verbrauchs- und
Integrationsdaten bleiben unverändert.
