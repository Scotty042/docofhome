# Validierung 1.7.4

## Automatisierte Prüfungen

- Versionsvertrag 1.7.4
- TypeScript-/Vue-Skriptsyntax
- MDI-Regressionsprüfung: gegenüber 1.7.3 wurden keine neuen Iconnamen eingeführt
- Releasevertrag 1.7.4
- bestehende Elektrointegritätsverträge
- bestehende Phasen-/Kammschienenverträge
- Migrationskette bis Alembic-Head 0049

## Neue statische Verträge

- Umschaltung `Übersicht / Verkabelung` vorhanden
- alte Option `Erweitert` entfernt
- N-/PE-Karten ohne eingebettete ausführliche Verkabelungszusammenfassung
- Detaildrawer enthält vor- und nachgelagerte Verbindungen
- vollständiger Reihenzähler ohne Null-Badge
- visuelle Leiterfarben L1/L2/L3/N/PE
- Dreieck für Hausanschluss
- Kreis/Viereck für externe Abgänge
- automatische Busbar-Einzelkontakte werden nicht mehrfach gezeichnet

## Manueller Smoke-Test

1. Schrankaufteilung öffnen und zwischen Übersicht und Verkabelung wechseln.
2. Prüfen, dass alle sichtbar platzierten Endpunkte korrekt verbunden werden.
3. Phasen-/Kammschiene prüfen: keine Linie pro einzelnem automatischem Kontakt.
4. Netzanschluss prüfen: Dreieck und passende Leiterlinien.
5. Abgang zu einer anderen Verteilung prüfen: externes Kreis-/Vierecksymbol.
6. DIN-Gerät öffnen und vor-/nachgelagerte Verbindungen prüfen.
7. N- und PE-Schiene in der Übersicht prüfen: keine ausführliche Einspeisungsbox.
8. L1/L2/L3-Chips im Dark Mode auf Lesbarkeit prüfen.
9. Leere Reihe prüfen: kein Badge. Belegte Reihe prüfen: vollständige Anzahl mit
   Beschriftung „Elemente“.

## In dieser Build-Umgebung nicht vollständig ausführbar

Der vollständige Lauf von `npm test` und `npm run build` war nicht möglich, weil
der konfigurierte NPM-Spiegel benötigte, im Lockfile festgelegte Pakete nicht
bereitstellte. Deshalb müssen `vue-tsc`, Vitest und der Vite-Produktionsbuild
beim Docker-Build beziehungsweise in der regulären CI erneut ausgeführt werden.
Die geänderten TypeScript-Skripte wurden zusätzlich mit TypeScript 5.8.3 und
lokalen Modulschnittstellen semantisch geprüft.
