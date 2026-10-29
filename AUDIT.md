# DocOfHome – aktueller Audit- und Qualitätsstatus

Stand: 29. Oktober 2026 · Release: 1.8.0 · Alembic-Head: `0060`

## Ergänzung 1.8.0

Basis ist der ausgelieferte und vom Nutzer installierte Stand 1.7.20, SHA256
`5458e47103b27fa1711122fcb344c4936dcb2d6514097eeb6e494706d1e40c95`.
Der Paketbau prüft jeden Basispfad gegen dessen vorhandenes Dateimanifest.
Keine vorhandene Quelldatei wird entfernt. Es wurde keine produktive Installation
geändert und kein GitHub-Release veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte Push-/LEGO-/MCP-/Backup-/Docker-/Migrationstests | 46 bestanden |
| Backend-Gesamtlauf | 318 bestanden, 30 fehlgeschlagen, 67 Warnungen (348 Tests) |
| Frontend-Gesamttests | 202 bestanden in 62 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Frontend-Produktionsbuild | bestanden; bestehende Bundlegrößenwarnung |
| Icon-Prüfung | 274 Icons verfügbar |
| Release-/Versions-/Branding-/Migrationsskripte | 38 bestanden |
| TypeScript-/Vue-Syntaxprüfung | 210 Skripteinheiten bestanden |
| Neue Push-Dateien: Ruff | bestanden |
| Ruff gesamt | 103 bestehende Meldungen |
| Mypy gesamt | 60 bestehende Meldungen in 15 Dateien; keine neuen Push-Meldungen |
| Frische Migration bis 0060 und 0059 → 0060 → 0059 → 0060 | bestanden |
| Schemaabgleich | bestehende Altabweichungen, keine Push-Abweichung |
| Docker-Image-Build und reale Smartphonezustellung | lokal nicht verfügbar, nicht ausgeführt |

Die Push-Tests verwenden die tatsächlichen HTTP-Clients mit isolierten
Serverantworten: Pushover-Formulardaten, ntfy-JSON und Bearer-Token, Unicode,
Entwurfstest ohne Speichern, tägliche Zusammenfassung für beide Dienste,
persistente Dublettenvermeidung über mehrere Sitzungen, abgelaufene Versandclaims,
unabhängige Fehler und maximal drei Versuche, Sommer-/Winterzeit, begrenzte
Nachrichtenlänge, ungültige Antworten und unterbundene Redirects.

Die Auswahl prüft bestehende monatliche Ableseregeln einschließlich erledigter
Ablesung, getrennte Kategorien, Ausschluss erledigter/archivierter Einträge und
keine doppelte Meldung automatisch erzeugter Zähleraufgaben. Backup und Restore
erhalten Konfiguration, Schlüssel und Versandmarker. Datenexporte enthalten weder
Schlüssel noch private Topics; auch Audit-Ereignisse maskieren geheime Systemwerte.
Diese Maskierung wurde beim neuen Exporttest ergänzt. Validierungsantworten der
neuen Einstellungs-API enthalten keine geheimen Eingabewerte.

Die neuen Oberflächentests führen das echte Seitenskript mit Vue-Reaktivität und
isolierten Antworten aus. Sie prüfen Entwurfstest, Speichern, Entfernen von
Schlüsseln, fehlerhaftes Speichern, Verwerfen und Schutz beim Verlassen/Neuladen.
Dies ersetzt keinen Browser-End-to-End-Test.

Automatischer Versand ist nach dem Update standardmäßig ausgeschaltet. Es wurden
keine echten Pushover-/ntfy-Nachrichten gesendet und keine Benutzerzugangsdaten
verwendet. Die Einrichtung erfordert einen Test des Empfangs auf dem eigenen
Smartphone. Ein angenommener API-Aufruf bestätigt keine Geräte-Zustellung; bei
unklarem Netzwerkergebnis ist trotz Versandmarkern eine Wiederholung möglich.

Die vollständige Qualitätsprüfung bleibt wegen der dokumentierten Altfehler
nicht grün. Die Protokolle liegen neben dem Paket unter validation-1.8.0.
Die Fehlernamen wurden mit den gespeicherten Läufen verglichen: Gegenüber
1.7.20 kommt ausschließlich der bereits in 1.7.19 dokumentierte datumsabhängige
Monatsregeltest hinzu. Er erwartet fest den 15. des aktuellen Monats, der am
29. Oktober bereits vergangen ist. Gegenüber der Fehlerliste von 1.7.19 gibt
es keinen neuen Fehlernamen. Die übrigen 29 Altfehler bleiben unverändert.

## Ergänzung 1.7.20

Basis ist der unveränderte Quellstand 1.7.19 mit SHA256
`339880ec0964b451ca188da5cc4fa08d97502fccf34369086d16487b5a8c40c2`.
Neu ist die LEGO-Sammlung. Alle bestehenden Quelldateien bleiben im Paket;
Manifest und Prüfsumme weisen Ergänzungen und Änderungen einzeln aus.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte LEGO-/MCP-/Backup-/Docker-/Migrationstests | 28 bestanden |
| Backend-Gesamtlauf | 301 bestanden, 29 fehlgeschlagen, 64 Warnungen (330 Tests) |
| Frontend-Gesamtlauf | 197 bestanden in 61 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Frontend-Produktionsbuild | bestanden; bekannte Bundlegrößenwarnung bleibt |
| Icon-Prüfung | 271 Icons verfügbar |
| Release-/Versions-/Branding-/Migrationsskripte | 38 bestanden |
| TypeScript-/Vue-Syntaxprüfung | 206 Skripteinheiten bestanden |
| Neue LEGO-Dateien: Ruff | bestanden |
| Ruff gesamt | 103 bestehende Meldungen |
| Mypy gesamt | 60 bestehende Meldungen in 15 Dateien, keine LEGO-Meldungen |
| Frische Datenbankmigration bis 0059 | bestanden |
| 0058 → 0059 → 0058 → 0059 mit vorhandenen Menüentscheidungen | bestanden |
| Schemaabgleich | bekannte Altabweichungen; keine LEGO-/Docker-Abweichung |
| Docker-Image-Build | lokal kein Docker verfügbar, nicht ausgeführt |

Die 29 fehlgeschlagenen Tests wurden anhand ihrer Namen mit dem gespeicherten
1.7.19-Gesamtlauf verglichen: kein neuer Fehler. Der seinerzeit zusätzlich
datumsabhängig fehlgeschlagene Monatsregeltest besteht am 5. Oktober.
Die vollständige Qualitätsprüfung ist damit weiterhin nicht grün. Die alten
Elektro-, Netzwerk-, Integrations- und Downgradefehler wurden nicht übersprungen.

Die neuen Backendtests prüfen normalisierte eindeutige Setnummern, exakte
Preiswerte, unbekannte gegenüber bekannten Nullwerten, ungültige Eingaben,
vollständige Seitennavigation, REST-Erstellen/Ändern/Löschen, echte MCP-Aufrufe
über Bearer und Tokenpfad, Schreibschutz und Erhalt nicht übergebener Felder.
JSON- und CSV-Roundtrips, Setnummerkonflikte bei anderer ID sowie vollständige
Sicherung/Wiederherstellung einschließlich lokalem Bild wurden ausgeführt.
Die Oberflächentests führen das tatsächliche Seitenskript mit Vue-Reaktivität
aus und prüfen Filter, unbekannte Werte und Schutz vor ungespeicherten Änderungen.
Dies ist kein Browser-End-to-End-Test.

Online-Kataloge werden von DocOfHome nicht automatisch abgefragt. Ein verbundener
Assistent kann recherchierte Angaben über MCP mit Quelle und Datum eintragen.
Verfügbarkeit und Verlässlichkeit der externen Angaben wurden hier nicht geprüft.
Es wurde keine produktive Installation geändert und kein GitHub-Release erstellt.
Der geprüfte Quellstand ist vor dem Einsatz im Ziel-Dockerimage zu testen.

## Ergänzung 1.7.19

1.7.19 baut unverändert auf dem bereitgestellten und praktisch getesteten 1.7.18-Stand auf.
Neu geprüft werden Mehrhost-Trennung, SSH-Befehlsbeschränkung, Host-Key-Pinning,
Migration einer vorhandenen Socket-Konfiguration und Sicherung der SSH-Schlüssel.
Es wurde keine produktive Installation verändert und kein GitHub-Release veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte Backendtests für 1.7.18/1.7.19 und Migrationen | 14 bestanden |
| Backend-Gesamttests | 286 bestanden, 30 fehlgeschlagen, keine Testaufbaufehler (316 Tests) |
| Frontend-Gesamttests | 192 bestanden in 60 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Frontend-Produktionsbuild | bestanden; Warnung wegen großem Hauptbundle bleibt |
| Icon-Prüfung | 270 Icons verfügbar |
| Release-, Versions- und statische Migrationsprüfungen | 38 Python-Prüfskripte bestanden |
| TypeScript-/Vue-Syntaxprüfung | 202 Skripteinheiten bestanden |
| Geänderte Backenddateien: Ruff | bestanden |
| Geänderte SSH-/Docker-Backenddateien: Mypy | bestanden |
| Ruff gesamt | 103 bestehende Meldungen verbleiben |
| Mypy gesamt | 60 Meldungen in 15 Dateien verbleiben |
| Frische Datenbankmigration bis 0058 | bestanden |
| Alembic-Schemaabgleich | nicht bestanden; ausschließlich bereits dokumentierte Altabweichungen, keine neue Docker-Host-Abweichung |
| Docker-Image und realer SSH-Zielserver | lokal nicht verfügbar, daher nicht ausgeführt |

Die neuen Tests prüfen zwei Hosts mit identischem Containernamen und identischer
Container-ID, getrennte Zuordnung zum jeweiligen Asset, Ed25519-Erzeugung und
Dateirechte, festes `known_hosts`, ausschließlich Public-Key-Anmeldung, Migration
der alten Socket-Konfiguration sowie den erzwungenen Serverbefehl. Der Helfer darf
nur `/version` und `/containers/json?all=1` abfragen. Backup und Restore wurden
einschließlich privater SSH-Schlüssel und der Rechte `0700`/`0600` geprüft.

Der Gesamtprüflauf ist weiterhin nicht grün. 29 Fehler entsprechen den bereits für
1.7.18 dokumentierten älteren Elektro-, Netzwerk-, Integrations- und
Downgrade-Prüfungen. Zusätzlich ist am Testdatum 17. September ein bestehender
Wiederholungsregeltest datumsabhängig fehlgeschlagen, weil er fest den bereits
vergangenen 15. des Monats erwartet. Keiner dieser Fehler betrifft die neuen
Mehrhost-/SSH-Tests. Sie wurden nicht übersprungen oder als bestanden dargestellt.

Die lokale Laufzeit nutzt Python 3.12.14 und Node 24.19.0. Das Zielimage sieht
Python 3.13.5 und Node 22.16 vor. Weder Docker noch ein erreichbarer SSH-Testserver
standen lokal zur Verfügung. Deshalb müssen Image-Build, Public-Key-Einrichtung,
Fingerabdruckvergleich und der erste echte NUC-Abgleich in einer isolierten
Testinstallation bestätigt werden.

## Historischer Prüfstatus 1.7.18

Stand: 8. September 2026 · Release: 1.7.18 · Alembic-Head: `0057`

## Lokaler Prüfstatus 1.7.18

**Das ZIP ist ein lokal gebauter Patch-Stand, keine vollständig grüne Produktionsfreigabe.**
Vor Einsatz in der laufenden Installation einen vollständigen externen Datenordner-Backup
erstellen und das Update zunächst in einer Testinstallation prüfen.

Basis ist unverändert die bereitgestellte 1.7.17-ZIP, SHA256
`7a50ebc3626d441dbf69cd0dd89d1adcbeb0ac0f1ac1e04483df33b94fd623b4`.
Die Release-Historie beschreibt Umfang und Kompatibilität. Das separate Dateimanifest
enthält den Vergleich jedes Quellpfads und die Prüfsumme jeder enthaltenen Datei.
Es wurde weder auf die produktive Installation zugegriffen noch ein Git-Tag veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Gezielte Backend-Regressionssuite | 47 bestanden |
| Backend-Gesamttests | 282 bestanden, 29 fehlgeschlagen, keine Testaufbaufehler (311 Tests) |
| Frontend-Gesamttests | 191 bestanden in 59 Dateien |
| Vue-/TypeScript-Typprüfung | bestanden |
| Produktionsbuild | bestanden; Warnung wegen großem Hauptbundle bleibt |
| Icon-Prüfung | 269 Icons verfügbar |
| TypeScript-/Vue-Syntaxprüfung | 201 Skripteinheiten bestanden; nutzt jetzt lokale Lockfile-Abhängigkeit |
| Release-/Versions-/Branding-/Migrationsskripte | alle 37 Python-Prüfskripte bestanden |
| Frische Datenbank bis Migration 0057 | bestanden |
| 0056 → 0057 mit ungültigem Altrezept, Rückmigration | bestanden; Zutaten und Schritte erhalten; SQLite-Integrität und Fremdschlüssel geprüft |
| Ruff für geänderte Backend-Implementierungen und neue Tests | bestanden |
| Ruff gesamt | 112 Meldungen verbleiben; vorher 217 |
| Mypy gesamt | 65 Meldungen in 16 Dateien; vorher 66 in 17 Dateien |
| Datenbankschemaabgleich | nicht bestanden; bestehende Index-, Fremdschlüssel- und Typabweichungen bleiben |
| Docker-/Linux-/Python-3.13-Build | lokal nicht verfügbar, nicht geprüft |

Die gezielten Tests führen echte MCP-Aufrufe gegen isolierte Testinstanzen aus:
36 registrierte Werkzeuge, mehrfacher Serverstart, ungültige Tokens, Schreibschutz,
Rezept-Speichern per Bearer und Suche per Token-Pfad, Profil-/Tätigkeitsdatenerhalt,
leere Rezeptliste und 101 Rezepte über mehrere Seiten. Ferner wurden eine Sicherung
mit lokalem Rezeptbild und Zeitplan in ein frisches Datenverzeichnis zurückgespielt,
Format 1 eingelesen, manipulierte Archive zurückgewiesen und Export/Import mit
binärem Historienanhang sowie Paperless-Verknüpfung verglichen. Die Frontendtests
führen das tatsächliche Einstellungs-Skript mit Vue-Reaktivität und isolierten
Netzwerkantworten aus. Clipboard verwendet nachgebildete Browserfunktionen;
dies ersetzt keinen End-to-End-Test auf einem realen Mobilbrowser.

Laufzeit: Python 3.12.14, MCP 2.0.1, FastAPI 0.116.2, SQLModel 0.0.42,
Node 24.19.0. Vorhandene lokale Entwicklungsabhängigkeiten wurden wiederverwendet.
Das Frontend-Lockfile wurde ausschließlich in den Versionsfeldern geändert.
Das Projekt verlangt Python 3.13; CI nutzt Node 22.16. Diese Zielumgebung
muss die lokalen Prüfungen noch bestätigen.

Die Gesamtprüfung ist weiterhin nicht grün: Ältere Upgrade-/Downgrade-Ketten
stoßen auf Fremdschlüsselverletzungen, Elektrotests verwenden teils überholte
Modelle oder erwarten frühere Beschriftungen. Daneben bleiben Fehler in
Netzwerk-, Home-Assistant- und Wiederholungsregel-Tests. Diese wurden nicht
pauschal übersprungen oder durch Abschalten von Prüfungen verdeckt.
Die vormals 105 Testaufbaufehler durch den globalen MCP-Lebenszyklus treten
nicht mehr auf; dadurch laufen zusätzliche Tests erstmals bis zu ihren
fachlichen Prüfungen. Weniger Testaufbaufehler bedeutet deshalb nicht
automatisch eine vollständig fehlerfreie Anwendung.

Der Schemaabgleich meldet weiterhin Unterschiede bei Home-Assistant-Linkindizes,
`network_interfaces.is_primary` und Smart-Meter-Indizes, `ON DELETE CASCADE`
sowie dem Typ der Notizspalte. Migration 0057 ändert diese Altbereiche nicht.
Weitergehende Zugriffskontrolle der REST-API und Ladezeitoptimierung sind
nicht Teil dieses Patches. Details zu den ausgeführten Prüfungen liegen
neben der ZIP im Ordner `validation-1.7.18`.

## Historische Auditnotizen bis 1.7.1

Stand: 28. Juli 2026
Release: 1.7.1
Alembic-Head: `0048`

## Einordnung

1.6.3.8 korrigiert die FI/RCD-Gruppenzuordnung für das seit 1.6.3.7 verbindliche
DIN-Asset-Modell. Das Auswahlfeld an Phasen-/Kammschienen und N-Schienen nutzte
noch ausschließlich historische `electrical_protective_devices`. Daher waren als
DIN-Assets platzierte FI-Schutzschalter nicht auswählbar.

## Integritätsregeln

- aktuelle FI/RCD und FI/LS werden als DIN-Assets derselben Verteilung angeboten;
- historische FI/RCD-Schutzgeräte bleiben rückwärtskompatibel;
- eine Schrankkomponente referenziert entweder einen historischen FI/RCD oder ein
  FI/RCD-Asset, niemals beide;
- nur aktive, platzierte Assets mit passendem FI/RCD-Asset-Typ sind zulässig;
- ein referenziertes FI/RCD-Asset kann erst nach dem Lösen der Zuordnung aus dem
  Verteilerschrank entfernt werden;
- vorhandene Kammschienen- und DIN-Kontaktlogik bleibt unverändert.

## Qualitätsnachweis

Ausgeführt wurden Versions-, Branding-, Elektro-, Kammschienen-, Python- und
TypeScript-/Vue-Syntaxprüfungen sowie sämtliche Migrationsprüfungen bis `0047`.
Der vollständige Pytest-, Ruff-, Mypy-, Vite- und Docker-Lauf benötigt die externen
Projektabhängigkeiten und ist auf dem Zielsystem auszuführen.


## Ergänzung 1.7.1

Der Abgleich gegen 1.7.0 hat einen fachlichen Modellkonflikt aufgelöst:
Stromkreise referenzierten dort ausschließlich historische Schutzgeräte,
während seit 1.6.3.7 neue Geräte als DIN-Assets angelegt werden. 1.7.1
unterstützt beide Referenzarten mit gegenseitigem Ausschluss und serverseitiger
Validierung. Eigenständige FI/RCD bleiben als Gruppen-Schutzgeräte von der
Zuordnung zu einem einzelnen Stromkreis ausgeschlossen.
