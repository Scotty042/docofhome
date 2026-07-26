# Validierungsbericht – DocOfHome 1.1.3

Stand: 23. Juli 2026

## Ursache

Der Docker-Build von 1.1.2 brach in `npm run build` bereits vor Vue-TSC und Vite
ab. Die vorgeschaltete Prüfung erkannte `mdi-ground-wire` als nicht vorhandenes
Icon in der festgeschriebenen Abhängigkeit `@mdi/font` 7.4.47.

## Korrektur

- einzige Verwendung von `mdi-ground-wire` entfernt;
- PE-Schiene auf `mdi-earth` umgestellt;
- Frontend-, Backend- und Releaseversion auf 1.1.3 vereinheitlicht;
- GitHub-CI von `npm install` auf das reproduzierbare `npm ci` umgestellt;
- keine Änderung an Datenmodell oder Migrationen.

## Lokal ausgeführte Prüfungen

- Quelltextsuche: keine verbleibende Verwendung von `mdi-ground-wire`;
- PE-Schienen-Konfiguration verwendet exakt `mdi-earth`;
- Versionskonsistenz zwischen `VERSION`, Frontend, Lockdatei und Backend;
- Python-Syntaxprüfung für Anwendung, Migrationen, Tests und Hilfsscripte;
- dependency-freie Vertragsprüfungen für Branding, Ableseerinnerungen und die
  zehn Funktionen aus 1.1.2;
- TypeScript-Syntaxprüfung der `.ts`-Dateien und der Scriptblöcke aus `.vue`
  mit dem lokal vorhandenen TypeScript-Parser;
- vollständige Manifest- und SHA-256-Prüfung nach erneuter Extraktion des
  finalen Release-ZIPs.

## Abhängigkeitsbasierter Build

Die Ausgangs-ZIP enthält keine installierten Node-Module. Gemäß der Vorgabe,
ausschließlich lokal mit dem gelieferten Projekt zu arbeiten, wurden keine
Pakete aus dem Internet nachgeladen. Der vollständige Lauf `npm ci && npm run
build` muss deshalb auf dem Docker-Zielsystem oder in GitHub Actions erfolgen.
Der konkret gemeldete Abbruchpunkt ist im Quellstand beseitigt; der vorhandene
MDI-Prüfschritt bleibt aktiv und schützt weiterhin vor unbekannten Icons.
