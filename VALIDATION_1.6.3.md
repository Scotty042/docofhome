# DocOfHome 1.6.3 – Validierungsbericht

Stand: 27. Juli 2026  
Ausgangsbasis: DocOfHome 1.6.2  
Schwerpunkt: vollständige Beziehungs- und Integritätsprüfung des Elektro-Moduls

## Prüfumfang

Die Prüfung wurde nicht auf einzelne Dialoge begrenzt. Untersucht wurden die
zusammenhängenden Abläufe und Beziehungen zwischen:

- Verteilungen, Feldern, Gerätebereichen und DIN-Platzierungen;
- Schutzgeräten, Phasen-/Kammschienen und allgemeinen Sammelschienen;
- FI/RCD-, FI/LS-, N- und PE-Beziehungen;
- manuellen und automatisch verwalteten Versorgungsverbindungen;
- wirksamen Phasen in Topologie, Stromkreisen und Verbrauchern;
- Smart-Meter-Messpunkten und den gemessenen Leitern;
- Archivierung, Verschieben, Typwechsel und Ersatz von Objekten;
- Bestandsmigrationen von 1.6.2 auf 1.6.3.

## Gefundene und korrigierte Fehlerklassen

### 1. Automatische Phasenschienen-Verbindungen

- Zulässige vorgelagerte Einspeisungen wie **FI/RCD → Phasenschiene** konnten
  von der Automatiksynchronisierung fälschlich als veraltete Schienenverbindung
  behandelt werden.
- Manuelle Verbindungen einer allgemeinen Sammelschiene zu Schutzgeräten konnten
  irrtümlich in die Kammschienen-Automatik geraten.
- Teilüberdeckungen und mehrere konkurrierende Phasenschienen waren nicht an
  allen Schreibwegen identisch abgesichert.

Korrektur: Automatisch verwaltet werden ausschließlich abgeleitete
**Phasenschiene → vollständig überdecktes Schutzgerät**-Verbindungen. Allgemeine
Sammelschienen und vorgelagerte Einspeisungen bleiben manuell und unangetastet.

### 2. Einheitliche Phasenberechnung

Die Berechnung der Außenleiter war zuvor auf mehrere Dienste verteilt. Dadurch
konnten Polzahl, Neutralleiterpol, Schienenstart und TE-Position unterschiedlich
interpretiert werden.

Korrektur: Eine gemeinsame Phasenkomponente berechnet das Muster für
Schrankansicht, Topologie, Automatiksynchronisierung und Migration. Bei RCD,
RCBO und SPD wird der Neutralleiterpol nicht als zusätzlicher Außenleiter
gezählt.

### 3. Stromkreis- und Verbraucherphasen

Ein Stromkreis konnte von einem L2-Schutzgerät versorgt werden, während eine
nachgelagerte Verbindung zum Verbraucher weiterhin als L1 dokumentiert wurde.

Korrektur: Stromkreise übernehmen eine eindeutige wirksame Außenleiterphase aus
Schutzgerät oder dokumentierter Einspeisung und geben sie verbindlich an
nachgelagerte Verbindungen weiter.

### 4. Smart-Meter-Messpunkte

Ein Messkanal konnte eine Phase auswählen, die auf der gemessenen Verbindung
nicht vorhanden war.

Korrektur: Messphasen werden gegen die wirksamen Leiter der Verbindung geprüft.
Bei genau einer wirksamen Außenleiterphase wird diese automatisch übernommen.
Beim Ersetzen einer automatischen Schienenverbindung bleiben Messpunkte erhalten
und werden korrekt umgehängt.

### 5. FI-, N- und PE-Beziehungen

- Eine N-Schiene konnte in einen anderen Komponententyp umgewandelt werden,
  obwohl Schutzgeräte sie noch referenzierten.
- FI/LS-Geräte konnten fälschlich wegen einer fehlenden separaten N-Schiene
  gewarnt werden.
- FI/RCD-Verweise waren nicht in allen Fällen auf fachlich passende
  Schienentypen begrenzt.

Korrektur: Typwechsel und Archivierung einer verwendeten N-Schiene sind
blockiert. Der RCBO-Sonderfall wird berücksichtigt. FI/RCD-Verweise sind nur an
Phasen- und N-Schienen erlaubt; PE-Schienen bleiben unabhängig.

### 6. Archivierung und Lebenszyklus

- Schutzgeräte konnten trotz aktiver manueller Zu- oder Abgangsverkabelung
  archiviert werden.
- Stromkreise konnten trotz aktiver Topologieverbindungen archiviert werden.
- Allgemeine Assets konnten trotz aktiver Elektroverbindungen archiviert,
  ersetzt oder an einen anderen Standort verschoben werden.
- Archivierte Stromkreise konnten aktive Asset-Zuordnungen hinterlassen.

Korrektur: Manuell dokumentierte Beziehungen müssen vor solchen Änderungen
bewusst gelöst werden. Nur automatisch abgeleitete Kammschienen-Verbindungen
werden intern synchronisiert.

### 7. Layout- und Platzierungsintegrität

Die Prüfungen für einfache Reihen, strukturierte Gerätebereiche und einzelne
Schreibwege waren nicht vollständig zentralisiert.

Korrektur: Kapazität, Bereichstyp, Kollision, vollständige Überdeckung,
Teilüberdeckung und konkurrierende Phasenschienen werden zentral validiert.
Eine Phasenschiene darf keine beliebigen DIN-Assets überdecken.

### 8. Datenbankintegrität und Bestandsreparatur

Migration `0043_release_1_6_3_electrical_integrity`:

- normalisiert Leiterfelder von Phasen-, N- und PE-Schienen;
- entfernt ungültige FI-Verweise und Phasenmetadaten anderer Komponententypen;
- rekonstruiert eindeutige automatische Kammschienen-Verbindungen;
- bewahrt legitime FI/RCD-Einspeisungen und manuelle Sammelschienen-Verbindungen;
- korrigiert nachgelagerte Außenleiter, Stromkreisverbindungen und Messphasen;
- ergänzt Datenbank-Constraints für Leiter, Phasenmetadaten und FI-Verweise.

## Erfolgreich ausgeführte Prüfungen

- zentrale Versionskonsistenz: `1.6.3`;
- Branding- und bestehende Korrekturverträge;
- neue Elektro-Integritäts- und Releaseverträge 1.6.3;
- Python-Syntax aller Backend-, Migrations-, Test- und Prüfscripte;
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten;
- Phasenschienen-Autoritätsprüfung;
- Migrationstests 0030, 0031, 0032, 0033, 0034, 0035, 0036, 0037,
  0039, 0040, 0041, 0042 und 0043;
- Migration 0043 einschließlich Upgrade, Datenreparatur, Constraints,
  Downgrade und erneutem Upgrade;
- finale ZIP-Kompressions-, Extraktions-, Versions- und Manifestprüfung.

## In dieser Build-Umgebung nicht ausführbare Gates

### Vollständige Backend-Pytest-Suite

Der Lauf wurde gestartet, brach aber bereits bei der Testsammlung ab, weil das
Python-Paket `sqlmodel` in der Umgebung nicht installiert ist:

```text
ModuleNotFoundError: No module named 'sqlmodel'
```

### Vollständiger Frontend-Build und Vitest

`npm ci` wurde gestartet. Der interne Paketserver antwortete beim Abruf einer
transitiven Abhängigkeit mit HTTP 503:

```text
npm error code E503
npm error 503 Service Temporarily Unavailable
```

Daher konnten `vue-tsc --noEmit`, Vite-Build und Vitest nicht mit frisch
installierten Projektabhängigkeiten ausgeführt werden. Die dependency-freie
TypeScript-/Vue-Syntaxprüfung war erfolgreich.

### Docker-Build

Docker ist in der Build-Umgebung nicht installiert (`docker: command not found`).
Ein Containerstart und Laufzeittest muss daher auf dem Zielsystem erfolgen.

## Updateprüfung auf dem Zielsystem

Vor dem Update ist der persistente `data`-Ordner vollständig zu sichern.
Anschließend:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs -f jarvis
```

Im Log muss das Alembic-Upgrade `0042 -> 0043` erfolgreich durchlaufen. Danach
Browsercache vollständig aktualisieren.

## Ergebnis

Die dependency-frei ausführbaren Prüfungen und sämtliche vorhandenen
Migrationsprüfungen waren erfolgreich. Die gefundenen systemischen Fehler im
Elektro-Modul wurden in Quellcode, Datenmodell, Migration, Frontendverhalten und
Dokumentation gemeinsam korrigiert. Die oben ausdrücklich genannten
abhängigkeits- und Docker-basierten Gates bleiben auf dem Zielsystem auszuführen.
## Nachträgliche Frontend-Build-Korrektur

Der beim Docker-Build gemeldete TypeScript-Fehler in
`frontend/src/pages/phaseRailAutoWiring.test.ts` wurde nachvollzogen. Ursache war ein
Import aus `node:fs`, obwohl der Frontend-`tsconfig.json` ausschließlich Browser-/Vite-Typen
lädt. Der Test verwendet nun denselben `?raw`-Import wie die bereits vorhandenen
Quellvertragstests. Zusätzlich prüft `scripts/check-release-1.6.3.py`, dass weder
`node:fs` noch `readFileSync` dort erneut eingeführt werden.

Ein vollständiger lokaler Wiederholungslauf von `npm run build` war in dieser Umgebung
nicht möglich, weil der interne npm-Paketserver beim Nachladen der Abhängigkeiten HTTP 503
lieferte. Der ursprüngliche Fehlerpfad wurde jedoch direkt beseitigt; alle anderen
Frontend-Quellvertragstests im Projekt verwenden bereits erfolgreich das gleiche
`?raw`-Muster.

## Nachprüfung: Drag-and-drop, Archivierung und automatische Kontakte

Nach Rückmeldung aus dem produktiven Docker-Build wurden drei zusätzliche
End-to-End-Pfade erneut untersucht:

1. Verschieben von Schutzgeräten innerhalb einer Phasen-/Kammschiene;
2. Archivieren direkt aus der Detailseitenleiste;
3. Erzeugung und Wiederherstellung der abgeleiteten Verbindung
   **Phasenschiene → Schutzgerät**.

### Gefundene Ursachen

- Die Oberfläche behandelte Phasenschienen beim Drag-and-drop für Schutzgeräte
  und allgemeine DIN-Assets gleich. Der Server unterschied korrekt, die
  Frontend-Vorprüfung übersprang die fachliche Unterscheidung jedoch vollständig.
  Das führte bei einem allgemeinen DIN-Asset erst nach dem Drop zu einer wenig
  verständlichen Servermeldung.
- Die Archivierungsfunktionen waren zwar in einzelnen Karten vorhanden, fehlten
  jedoch in der zentralen Detailseitenleiste.
- Die Automatiksynchronisierung konnte direkt vor dem Commit auf noch nicht
  geflushte Änderungen treffen. Außerdem bestand für einen bereits fehlerhaften
  Bestandsstand kein selbstheilender Abgleich beim Öffnen der Topologie.

### Korrekturen

- Vollständig von einer Phasenschiene überdeckte Schutzgeräte dürfen wieder
  verschoben werden. Teilüberdeckungen bleiben gesperrt.
- Allgemeine DIN-Assets werden unter einer Phasenschiene weiterhin bewusst
  abgewiesen; die Meldung bezeichnet das gezogene Objekt nun ausdrücklich als
  allgemeines DIN-Asset.
- Schutzgeräte und Schrankkomponenten besitzen in der Detailseitenleiste eine
  Archivieren-Aktion. Fehler werden innerhalb der Detailansicht angezeigt.
- Beim Archivieren einer Phasenschiene bleiben die Schutzgeräte platziert. Alle
  aktiven Verbindungen der Schiene werden atomar historisch archiviert.
- Die Synchronisierung flusht neue oder verschobene Schienen und Schutzgeräte,
  bevor die Kontaktverbindungen abgeleitet werden.
- Topologie und Verbindungsliste führen einen selbstheilenden Abgleich aktiver
  Phasenschienen aus. Fehlende abgeleitete Kontakte werden rekonstruiert und
  konkurrierende manuelle Einspeisungen des Schutzgeräts sauber ersetzt.
- Der stabile Abgleich ist idempotent und verändert Zeitstempel nur bei einer
  tatsächlichen fachlichen Änderung.

### Ausgeführte Prüfungen

- Python-Syntaxprüfung für Anwendung, Migrationen und Tests;
- Syntaxprüfung von 181 TypeScript-/Vue-Skripteinheiten;
- Versions-, Branding-, gesammelte Fixes-, Ableseerinnerungs-,
  Phasenschienen- und Elektro-Integritätsverträge;
- alle dependency-freien Migrationsprüfungen 0030 bis 0043;
- ergänzte Regressionstestquellen für Selbstheilung und Archivierung einer
  belegten Phasenschiene;
- Quellvertragstest für Detail-Archivierung und korrekte DnD-Unterscheidung.

### Nicht erneut vollständig ausführbar

Die vollständige SQLModel/Pytest-Suite konnte nicht gestartet werden, da die
Python-Abhängigkeiten in der isolierten Build-Umgebung nicht verfügbar waren.
`npm ci` konnte ebenfalls keine vollständigen Pakete beziehen; daher waren
`vue-tsc`, Vitest und Vite hier nicht erneut ausführbar. Der vom vorherigen
Release bekannte Node-Builtin-Import ist weiterhin entfernt. Alle geänderten
Dateien wurden mit den verfügbaren dependency-freien Syntax- und
Vertragsprüfungen geprüft.
