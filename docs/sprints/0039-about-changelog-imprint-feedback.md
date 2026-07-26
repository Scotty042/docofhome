# Sprint 0039 – Über DocOfHome, Changelog, Impressum und Feedback

- Status: Completed
- Zielrelease: 1.4.1
- Abhängigkeiten: Release 1.2.3, bestehende Nextcloud-WebDAV-Integration

> Mit Release 1.4.1 umgesetzt und mit 1.4.2 vereinfacht. Das konfigurierbare
> Impressum wurde entfernt. Projektlinks liegen nun im Quellcode und Feedback
> wird direkt als ZIP an einen festen öffentlichen Nextcloud File Drop gesendet.

## Ziel

DocOfHome erhält eine zentrale, verständliche Informationsseite. Betreiber und
Nutzer sollen Zweck, Version, Änderungen, Projektverweise und Impressumsangaben
finden und optional strukturiertes Feedback übermitteln können.

## Fachlicher Umfang

### 1. Seite „Über DocOfHome“

Navigation: **Mehr → Über DocOfHome**

Abschnitte oder Tabs:

- **Projekt** – kurzer Text zu Zweck, Motivation, lokaler Hausdokumentation und
  Datenhoheit;
- **Versionen & Changelog** – aktuelle Version, Veröffentlichungsdatum und
  versionierte Änderungen;
- **Feedback** – optionales Formular;
- **Impressum** – nur konfigurierte Felder anzeigen.

### 2. Projekt- und GitHub-Hinweise

Konfigurierbar:

- Projektwebseite;
- Repository-URL;
- Release-URL;
- Issue-/Feedback-URL;
- Lizenzhinweis.

Ist keine URL gesetzt, darf keine tote oder erfundene Verknüpfung angezeigt
werden.

### 3. Changelog

- aktuelle Version aus der zentralen Versionsquelle lesen;
- Changelog und Release Notes nicht mehrfach manuell im Frontend pflegen;
- sichere Markdown-Darstellung ohne ausführbares HTML;
- ältere Versionen einklappbar darstellen.

### 4. Impressum

Konfigurierbare Felder:

- Betreibername beziehungsweise Organisation;
- ladungsfähige Anschrift;
- E-Mail-Adresse;
- optionale Telefonnummer;
- verantwortliche Person;
- optionale Register-/Umsatzsteuerangaben;
- optionaler Freitext.

Leere Felder werden nicht angezeigt. Persönliche Angaben dürfen nicht Bestandteil
des Standard-Releases sein.

### 5. Feedbackformular

Mindestens:

- Kategorie: Fehler, Verbesserung, Bedienung, Dokumentation, Sonstiges;
- Betreff;
- Beschreibung;
- optional aktuelle Seite;
- optional technische Informationen nach sichtbarer Zustimmung.

Der Nutzer sieht vor dem Absenden, welche Metadaten übertragen werden. Secrets,
Tokens, Passwörter, vollständige Konfigurationen und ungefragte personenbezogene
Daten sind ausgeschlossen.

## Nextcloud-Übertragung

- Übertragung ausschließlich über das DocOfHome-Backend;
- keine WebDAV-Zugangsdaten oder Freigabetokens im Browser;
- eigener Nextcloud-Benutzer beziehungsweise App-Passwort mit Zugriff nur auf
  den Feedbackordner;
- Speicherung als UTF-8-Text- oder Markdown-Datei;
- serverseitig erzeugter, sicherer Dateiname mit Zeitstempel und Zufallsanteil;
- kontrollierter Zielpfad ohne frei eingebbare Pfadsegmente;
- Verbindungstest in den Einstellungen;
- verständliche Fehlermeldung ohne Preisgabe von Secrets.

## Sicherheitsanforderungen

- Feedbackfunktion standardmäßig deaktiviert;
- Zielhost-Validierung und SSRF-Schutz analog zu bestehenden Integrationen;
- TLS-Prüfung standardmäßig aktiv;
- keine unkontrollierten Redirects;
- Größenlimit für Text und Anhänge;
- Rate-Limit;
- Dateinamen niemals direkt aus Betreff oder Benutzertext ableiten;
- sensible Konfigurationsfelder in API, Audit und Export redigieren;
- Upload nur als explizite Benutzeraktion;
- definierte Timeouts und begrenzte Antwortgrößen.

## Noch offene Entscheidungen vor „Approved“

1. Soll Feedback zusätzlich lokal gespeichert beziehungsweise bei Ausfall
   zwischengespeichert werden?
2. Sind Anhänge oder Screenshots im ersten Umfang enthalten?
3. Welche technischen Metadaten sind optional auswählbar?
4. Wie lange sollen Feedbackdateien aufbewahrt werden?
5. Reicht das bestehende private Netzwerk als Zugriffsschutz oder muss zuerst
   Authentifizierung umgesetzt werden?
6. Welche Online-/GitHub-Felder sollen standardmäßig sichtbar sein?
7. Wie wird das Impressum bei ausschließlich privater Nutzung ausgeblendet?

## Nicht im Umfang

- automatisches Erstellen von GitHub-Issues;
- öffentliches anonymes Feedback ohne Zugriffsschutz;
- Telemetrie oder automatische Nutzungsanalyse;
- ungefragte Übertragung von Diagnose- oder Systemdaten;
- allgemeiner Nextcloud-Dateibrowser.

## Akzeptanzkriterien

Diese Kriterien sind vor Freigabe zu vervollständigen. Mindestziel:

- Info-Seite ist auf Desktop und Mobilgeräten erreichbar;
- Version und Changelog stammen aus zentralen Quellen;
- Impressumsfelder sind konfigurierbar und standardmäßig leer;
- GitHub-Hinweise erscheinen nur bei hinterlegten URLs;
- Feedback kann optional sicher über das Backend nach Nextcloud übertragen
  werden;
- Browser erhält niemals WebDAV-Secrets;
- Fehlerfälle, Größenlimits, Rate-Limit und SSRF-Schutz sind getestet;
- Dokumentation, Migrationen und Backupverhalten sind geklärt.
