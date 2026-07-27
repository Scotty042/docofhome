# DocOfHome 1.6.2 – Validierungsbericht

Stand: 27. Juli 2026  
Ausgangsbasis: `DocOfHome-1.6.1.zip`  
SHA-256 der Ausgangsbasis: `07e92ea167921d05c65bc24e888b9e6407fa3bc5c962a29c88ed209c131cd8bf`

## Umgesetzter Prüfumfang

DocOfHome 1.6.2 übernimmt die Korrekturen aus dem Runbook vom 27. Juli 2026 auf
Basis von 1.6.1. Der Schwerpunkt dieses Releases liegt auf:

- idempotenten monatlichen Zähler-Ableseaufgaben;
- getrennten Dashboardwerten für PV-Erzeugung und Netzeinspeisung;
- wirksamen Phasen und sichtbaren Warnungen bei alten Phasenwidersprüchen;
- Verteilungen als strukturellen Behältern sowie dem Aufbau Verteilerdose;
- Kamm-/Phasenschienen ohne eigene TE-Belegung;
- dauerhaft im ZIP enthaltenen Repository- und Releaseinformationen.

Die bereits in 1.6.1 vorhandenen Korrekturen für letzten Zählerwert, OBIS-Hinweise,
Zählerwechsel, Bildsuchquellen, Schutzgerätezählung, vertikale Beschriftung,
direkte Asset-Verbindungen und den Asset-Typ „Smartes Relais / DIN-Schaltaktor“
bleiben erhalten und werden durch den Release-Vertragscheck mitgeprüft.

## Erfolgreich ausgeführte Prüfungen

- Versionskonsistenz: `VERSION`, Backend, Frontend und Lockdatei = `1.6.2`.
- Branding- und bestehende Korrekturverträge: bestanden.
- Release-Vertragsprüfung 1.6.2: bestanden.
- Python-AST-Prüfung aller 19 geänderten Python-Dateien: bestanden.
- Prüfung geänderter Python-Dateien auf die konfigurierte Zeilenlänge: bestanden.
- JSON- und Whitespace-Prüfung aller geänderten Dateien: bestanden.
- TypeScript- und Vue-`script setup`-Syntax: 179 Einheiten bestanden.
- Nach dem gemeldeten Vue-TSC-Fehler in `AssetDuplicateDialog.vue` wurde
  `junction_box` aus der Auswahl für fortlaufende DIN-Serienplatzierung
  ausgeschlossen. Die TypeScript-Narrowing-Regel wurde mit `tsc --noEmit
  --strict` isoliert erfolgreich geprüft.
- Quellweite Suche: keine weitere Stelle weist `DistributionLayoutMode` einer
  engeren Typmenge `"rows" | "sections"` ungefiltert zu.
- Die Schienen-Kollisionslogik unterscheidet nun TE-belegende Geräte von
  Overlay-Schienen. Ein Regressionstest deckt DIN-Assets unter einer Schiene,
  parallele Schienen auf unterschiedlichen Montageseiten und die Ablehnung einer
  zweiten Schiene auf derselben Montageseite ab.
- Der neue Regressionstest ist im Backend-Testbestand enthalten. Seine statische
  Syntax- und Vertragsprüfung ist bestanden; der vollständige Pytest-Lauf bleibt
  wegen der fehlenden Laufzeitabhängigkeiten in dieser Umgebung offen.
- Verkabelungen an Schutzgeräten mit wirksamer Schienenphase werden nun zweifach
  abgesichert: Der Dialog setzt die berechnete Außenleiterphase automatisch und
  sperrt die freie Auswahl von L1/L2/L3; das Backend erzwingt dieselbe Phase auch
  bei direkten API-Aufrufen. N und PE bleiben unabhängig auswählbar.
- Ein zusätzlicher Backend-Regressionstest bildet eine Sicherung auf TE 3 unter
  einer bei L1 startenden Dreiphasenschiene ab und erwartet für eine fälschlich
  als L1 gesendete Verkabelung die gespeicherte Phase L3.
- Speichermeldungen für Schrankkomponenten und Versorgungsverbindungen werden im
  jeweils geöffneten Dialog angezeigt, nicht mehr hinter dessen Overlay.
- Shell-Syntax des zentralen Prüflaufs: bestanden.
- Dependency-freie Migrationsprüfungen 0030 bis 0037: bestanden.
- Migration 0039: Upgrade, eindeutige Automationsschlüssel, Downgrade und
  erneutes Upgrade gegen SQLite bestanden.
- Automatische Ableseaufgaben: Quellvertrag für Erzeugung, Reaktivierung,
  automatische Erledigung und Schutz vor manueller Änderung bestanden.
- ZIP-Inhalte enthalten `SOURCE_INFO.json` und feste GitHub-/Release-/Issue-Links,
  unabhängig von einem `.git`-Verzeichnis.

## In dieser Build-Umgebung nicht vollständig ausführbare Gates

Die Ausgangs-ZIP enthält bewusst keine installierten Python- oder
Node-Abhängigkeiten. Die Ausführungsumgebung konnte keine externen Pakete
nachladen. Daher waren folgende vollständige Gates hier nicht möglich:

- Backend-Pytest: Abbruch vor Teststart, weil das Paket `sqlmodel` nicht
  installiert ist.
- Ruff und mypy: die Programme sind in der Umgebung nicht installiert.
- `npm ci`, Vitest, Vue-TSC und Vite-Build: die erforderlichen npm-Pakete waren
  weder installiert noch im Offline-Cache vorhanden.
- Docker-Compose-Build und Healthcheck: Docker ist in der Umgebung nicht
  installiert.

Die zugehörigen Tests, Lockdateien, Dockerdateien und CI-Prüfschritte sind im
Release enthalten. Vor einem produktiven Update sollte der normale
Docker-/GitHub-CI-Lauf deshalb zusätzlich vollständig durchlaufen.

## Daten- und Migrationssicherheit

- Migration 0039 überschreibt keine Zählerstände, Assets, Dokumente,
  Produktbilder oder bestehenden elektrischen Verbindungen.
- Alte widersprüchliche Verbindungsphasen bleiben gespeichert und werden
  zusätzlich mit den wirksamen Phasen und einer Warnung angezeigt.
- Ein Wechsel zur oder von einer Verteilerdose wird blockiert, solange noch
  Schutzgeräte, DIN-Platzierungen, Schrankkomponenten oder Felder vorhanden sind.
- Automatisch erzeugte Ableseaufgaben werden über einen eindeutigen Schlüssel
  idempotent verwaltet.

Vor dem Update ist trotzdem ein vollständiges Backup des persistenten
`data`-Ordners erforderlich.
