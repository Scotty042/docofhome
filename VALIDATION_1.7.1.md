# Validierung DocOfHome 1.7.1

Stand: 28. Juli 2026

## Zusammenführung

Verglichen wurden die Quellstände 1.6.3.5, 1.6.3.8 und 1.7.0. Änderungen aus
1.6.3.8 wurden nicht pauschal über 1.7.0 kopiert, sondern datei- und
funktionsbezogen zusammengeführt. Besondere Konfliktbereiche waren
Versionsdateien, Migrationsnummern, Asset-Codevergabe, DIN-Geräte,
FI/RCD-Zuordnung und die Stromkreis-Sicherungsreferenz.

## Verbindliche Prüfpunkte

- Migrationskette ist linear: `0045 -> 0046 -> 0047 -> 0048`.
- Fehlende Asset-Codezähler werden repariert und zur Laufzeit rekonstruiert.
- FI/RCD-Schienenverweise unterstützen historische Geräte und aktuelle
  DIN-Assets, jedoch niemals gleichzeitig.
- Stromkreise akzeptieren genau eine Schutzgerätereferenz.
- Aktuelle DIN-Sicherungen, LS und FI/LS/RCBO sind auswählbar.
- Eigenständige FI/RCD und nicht schützende DIN-Geräte sind nicht auswählbar.
- Belegte Schutzgeräte werden gekennzeichnet und können nicht doppelt verwendet
  werden.
- Verknüpfte FI/RCD- oder Stromkreis-Schutzassets können nicht unbemerkt aus
  dem Verteiler entfernt werden.
- Sämtliche 1.7.0-Funktionen für Zähler, Netzwerk, Bilder, Switch-Ansicht,
  Aufgaben, Dialogmeldungen und Phasenherkunft bleiben enthalten.

## Durchgeführte technische Prüfungen

Erfolgreich ausgeführt wurden:

- Python-Syntaxprüfung für Backend, Tests und Prüfscripte über `compileall`;
- `python scripts/check-version.py`;
- `python scripts/check-release-1.7.1.py`;
- isolierte Upgrade-/Downgrade-Prüfungen der Migrationen `0046`, `0047` und `0048`;
- Syntaxprüfung von 182 TypeScript-/Vue-Skripteinheiten;
- Branding-, gesammelte Fix-, Elektrointegritäts-, Phasenschienen- und
  Ableseerinnerungs-Verträge;
- Prüfung auf doppelte Alembic-Revisionsnummern, Konfliktmarker und fehlerhafte
  Git-Diffs.
- Prüfung aller im Quelltext referenzierten MDI-Icons; die leere IP-Ansicht
  verwendet nun das in `@mdi/font 7.4.47` vorhandene `mdi-ip-outline`.
- Prüfung der nach 1.7 erweiterten Frontend-Typverträge: Asset-Entwürfe
  enthalten die verpflichtenden Bildfelder und Test-Fixtures bilden die
  vollständigen `Asset`-, `AssetType`-, `ElectricalCircuit`- und
  `ElectricalConnection`-Antworten ab.
- Die sieben von der Fehlermeldung betroffenen TypeScript-Produktions- und
  Testdateien wurden zusammen mit ihren lokalen Abhängigkeiten zusätzlich mit
  TypeScript 5.8.3 kompiliert; die gemeldeten Typfehler treten dabei nicht mehr
  auf. Für `vue` und `vitest` wurden wegen des nicht erreichbaren Paketspiegels
  ausschließlich temporäre Ambient-Deklarationen verwendet, die nicht im
  Release enthalten sind.

In der abgeschotteten Build-Umgebung konnten der vollständige Pytest-/Ruff-/Mypy-Lauf
sowie `npm test`, `vue-tsc` und der Vite-Produktionsbuild nicht ausgeführt werden,
weil die Python-Abhängigkeit `sqlmodel` nicht lokal vorhanden war und der interne
NPM-Spiegel die benötigten Pakete wiederholt mit HTTP 503 abwies. Die gemeldeten
`vue-tsc`-Fehler wurden vollständig anhand ihrer Typverträge korrigiert. Ein
erneuter realer Docker-/Vite-Build sowie ein Alembic-Upgrade gegen eine Kopie der
produktiven Datenbank bleiben vor dem produktiven Einsatz verpflichtend.

## Manuelle Smoke-Tests

Zusätzlich zu den Smoke-Tests aus dem Runbook:

1. DIN-Asset „Sicherungsautomat“ platzieren und einem Stromkreis zuordnen.
2. Dasselbe DIN-Asset bei einem zweiten Stromkreis auswählen: muss blockiert
   oder als belegt dargestellt werden.
3. Das zugeordnete DIN-Asset aus dem Schrank entfernen: muss blockiert werden.
4. Eigenständigen FI/RCD platzieren: darf nicht als Endschutzgerät eines
   einzelnen Stromkreises angeboten werden.
5. FI/RCD-DIN-Asset einer Phasen- oder N-Schiene zuordnen und anschließend
   Entfernung aus dem Schrank prüfen.
6. Ein Asset eines per Migration angelegten Typs ohne Codezähler erstellen und
   fortlaufenden DocOfHome-Code prüfen.
