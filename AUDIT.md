# DocOfHome – aktueller Audit- und Qualitätsstatus

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
