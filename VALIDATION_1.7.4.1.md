# Validierung 1.7.4.1

## Automatisierte Prüfungen

- Versionsvertrag 1.7.4.1
- Releasevertrag 1.7.4.1
- TypeScript-/Vue-Skriptsyntax
- MDI-Iconprüfung
- bestehende Elektrointegritätsverträge
- bestehende Phasen-/Kammschienenverträge
- Migrationskette bis Alembic-Head 0049

## Neue Verträge

- Stromkreis-Endpunkte werden im Schrank-Overlay herausgefiltert.
- LS-/MCB- und FI/LS-/RCBO-Abgänge einzelner Stromkreise werden nicht gezeichnet.
- Direkte ältere Sicherung-zu-Stromkreis-Abzweige werden ebenfalls ausgeblendet.
- Mehrfachanschlüsse an einem Endpunkt erhalten getrennte Portpositionen.
- Verbindungen erhalten nach Routing-Kategorie getrennte Spuren.
- Eine Konturlinie trennt Leiter an Kreuzungen optisch.
- Die Bedienoberfläche weist ausdrücklich darauf hin, dass nur die
  Hauptverkabelung dargestellt wird.

## Manueller Smoke-Test

1. Verteilung mit mehreren Stromkreisen in der Ansicht „Verkabelung“ öffnen.
2. Prüfen, dass keine Leitung zu einzelnen LS-/RCBO-Stromkreisen erscheint.
3. Prüfen, dass Hausanschluss, Vorsicherung, Zähler, Phasenverteiler, FI/RCD,
   Schienen und Unterverteilungen weiterhin verbunden dargestellt werden.
4. Mehrere Leitungen an einem Hauptgerät prüfen: Anschlusspunkte und horizontale
   Spuren dürfen nicht exakt übereinanderliegen.
5. Kreuzende Leiter prüfen: Die dunkle Kontur muss die Leitungen voneinander
   abgrenzen.
6. Versorgungstopologie und Detaildrawer prüfen: ausgeblendete Stromkreiswege
   müssen dort weiterhin vollständig vorhanden sein.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0049`.

## Einschränkung der Build-Umgebung

Der vollständige Frontend-Build konnte in dieser Umgebung nicht ausgeführt
werden, weil der konfigurierte NPM-Spiegel benötigte Pakete mit HTTP 404 nicht
bereitstellte. Der geänderte Vue-Scriptblock wurde zusätzlich mit TypeScript
5.8.3 im Strict-Modus semantisch geprüft; die SFC-Template-Struktur wurde
separat geparst. Der reguläre Docker-Build muss `vue-tsc` und Vite nochmals
vollständig ausführen.
