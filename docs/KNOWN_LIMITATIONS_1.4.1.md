# Bekannte Grenzen DocOfHome 1.4.1

Stand: 25. Juli 2026

## Zugriffsschutz

DocOfHome besitzt weiterhin keine Benutzeranmeldung und ist für ein
vertrauenswürdiges privates Netzwerk vorgesehen. Die Anwendung darf nicht ohne
zusätzlichen vorgeschalteten Zugriffsschutz öffentlich aus dem Internet
erreichbar sein. Dies gilt besonders, wenn Impressums- oder Feedbackangaben
gepflegt werden.

## Info-Seite und Changelog

- Die Versionshistorie wird aus den mit dem Release ausgelieferten
  `RELEASE_NOTES_*.md`-Dateien gelesen. Nachträglich nicht in den Container
  kopierte Dateien erscheinen dort nicht.
- Die sichere Markdown-Darstellung unterstützt bewusst nur Überschriften,
  Absätze, einfache Listen und Codeblöcke. Eingebettetes HTML, Bilder und
  komplexe Markdown-Tabellen werden nicht ausgeführt beziehungsweise nicht
  besonders formatiert.
- Projekt-, Repository-, Release- und Issue-Verweise werden nur angezeigt, wenn
  sie in den Einstellungen hinterlegt wurden.

## Impressum

Das Impressum ist standardmäßig leer und wird nur eingeblendet, wenn mindestens
ein Feld gepflegt wurde. DocOfHome prüft nicht, welche Angaben im konkreten
Betriebsfall rechtlich erforderlich sind.

## Feedback

- Feedback ist standardmäßig deaktiviert.
- Für die Übertragung wird eine aktivierte und vollständig konfigurierte
  Nextcloud-Integration benötigt.
- Im ersten Umfang gibt es keine Anhänge, Screenshots, lokale Warteschlange oder
  automatische GitHub-Issue-Erstellung.
- Schlägt die Übertragung fehl, bleibt der Text im geöffneten Formular, wird aber
  nicht automatisch zwischengespeichert.
- Das einfache Rate-Limit wird pro laufendem Backend-Prozess im Arbeitsspeicher
  geführt und ist kein verteilter Missbrauchsschutz.

## Dashboard und Zählererfassung

Der Dashboard-Button öffnet direkt den normalen Ablesedialog und wählt den ersten
verfügbaren Zähler vor. Bei mehreren Zählern muss der gewünschte Zähler im
Dialog ausgewählt werden. Eine geführte Serienablesung aller Zähler ist noch
nicht enthalten.

## Elektro-Dokumentation

Die mit 1.4.0 eingeführte FI-, N-Schienen- und Sammelschienenlogik bleibt bewusst
eine private Hausdokumentation. Nummerierte Einzelklemmen, Aderlisten,
Kurzschluss- oder Selektivitätsberechnungen und eine normgerechte
Elektro-CAD-Ausgabe sind weiterhin nicht Bestandteil der Anwendung.
