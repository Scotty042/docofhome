# DocOfHome 1.6.3.4 – Validierungsbericht

Stand: 28.07.2026

## Anlass

In 1.6.3.2 wurde beim Speichern einer sichtbaren Phasen-/Kammschiene weiterhin
`automatisch mit 0 Schutzgerät(en) verbunden` gemeldet. Damit war belegt, dass
der implizite Synchronisationslauf keine passenden Geräte erkannte und trotzdem
eine irreführende Erfolgsmeldung zurückgab.

## Korrektur

- Nach dem Speichern einer Phasen-/Kammschiene ruft das Frontend einen eigenen
  Synchronisations-Endpunkt auf.
- Die Verteilerschrankansicht übermittelt alle aktuell sichtbaren Schutzgeräte-IDs
  der Verteilung. Fragile Frontend-Filter auf `deleted_at`, Platzierungsfelder oder
  optionale Bestandsattribute wurden entfernt.
- Das Backend lädt jedes gemeldete Schutzgerät direkt aus
  `electrical_protective_devices`, `electrical_components` und `assets`.
- Serverseitig werden Verteilung, Bereich, Reihe, vollständige TE-Überdeckung,
  Lebenszyklus und berechenbare Phase geprüft.
- Für jedes passende Gerät wird eine aktive, schreibgeschützte Verbindung
  `Phasen-/Kammschiene -> Schutzgerät` erzeugt oder reaktiviert.
- Alte konkurrierende Einspeisungen werden vor Aktivierung des automatischen
  Kontakts archiviert; Messpunktbezüge werden auf den neuen Kontakt umgehängt.
- Werden sichtbare Geräte gemeldet, aber kein Kontakt erzeugt, antwortet der
  Endpunkt mit einem konkreten Diagnosefehler je Gerät. Eine erfolgreiche
  Rückgabe mit `0 Schutzgerät(en)` ist in diesem Fall ausgeschlossen.
- Scheitert die Synchronisation nach dem erstmaligen Anlegen, bleibt der Dialog
  im Bearbeitungsmodus, damit beim erneuten Speichern keine doppelte Schiene
  entsteht.

## Ausgeführte Prüfungen

Erfolgreich:

- Versionskonsistenz 1.6.3.4
- Branding- und Releaseverträge
- Elektro-Integritätsverträge
- Laufzeitvertrag der Kammschienen-Synchronisation
- dependency-freier SQLite-Test für L1/L2/L3 und den Austausch einer bestehenden
  Einspeisung unter historischem Eindeutigkeitsindex
- Python-Syntax aller Backend-, Migrations-, Test- und Prüfscripte
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten
- Migrationsprüfungen 0030 bis 0044
- Releaseprüfung aus einem frisch entpackten ZIP
- ZIP-Kompressions- und Manifestprüfung

Nicht vollständig ausführbar:

- `npm ci` / `npm run build`: Der konfigurierte npm-Paketserver lieferte beim
  Abruf von `why-is-node-running-2.3.0.tgz` HTTP 503.
- vollständige Pytest-/Alembic-Anwendungssuite: Die benötigten externen
  Python-Abhängigkeiten konnten in dieser Umgebung nicht aus dem Paketserver
  installiert werden.

## Datenbank

Keine neue Migration erforderlich. Alembic-Head bleibt `0044`.
