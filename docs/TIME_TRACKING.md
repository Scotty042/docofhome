# Zeiterfassung

Unter **Alltag → Zeiterfassung** Ticketnummer und Kundenname eingeben, optional weitere Info ergänzen und **Start** drücken. Unter Einstellungen → Module lässt sich die Zeiterfassung samt Menüeintrag schalten.

- **Pause** schließt den Arbeitslauf ab und gibt den Timer für andere Tickets frei.
- **Ende** schließt den Arbeitslauf als beendet ab.
- **Tickets wieder aufnehmen** startet einen weiteren Arbeitslauf mit den zuletzt verwendeten Ticketdaten. Auch beendete Tickets können erneut aufgenommen werden.
- Es läuft immer höchstens ein Timer gleichzeitig. Beim Wechsel zuerst Pause oder Ende drücken.

Der Verlauf unten zeigt standardmäßig die letzten 30 Kalendertage einschließlich heute, die gesamte Arbeitszeit ohne Pausen sowie Ticketsummen. Alle Arbeitsläufe sind chronologisch mit Ticket, Kunde, Info, Anfang, Ende und Dauer sichtbar. Die Schnellauswahl bietet Heute, Gestern, letzte 7/30/90/365 Tage, diesen/letzten Monat und dieses/letztes Jahr. Von und Bis einschließlich erlauben eigene Zeiträume; Aktualisieren lädt die Daten neu. Für die Tagessumme Heute wählen. Arbeitsläufe über Mitternacht werden für die Summen anteilig auf beide lokalen Kalendertage verteilt. Die Anzeige verwendet die Zeitzone des Browsers. Gleiche Ticketnummern werden exakt nach Entfernung führender und nachfolgender Leerzeichen gruppiert.

Der Timer wird in der Datenbank gespeichert und verwendet die Serverzeit. Schließen der Seite oder ein Neustart beendet ihn nicht. Andere geöffnete Ansichten werden spätestens nach 15 Sekunden aktualisiert. Bei einem Verbindungsfehler bleibt der zuletzt bestätigte Timer aktiv; nach Wiederverbindung kann er beendet werden.

Migration **0062** ergänzt die Tabelle und aktiviert das neue Modul bei bestehenden Installationen. Es wurde keine produktive Datenbank geändert. Vor Nutzung den regulären Updateprozess inklusive Migration und Frontend-Build ausführen.

Die aktuelle Fassung ist eine gemeinsame persönliche Zeiterfassung ohne Benutzerzuordnung. **Manuellen Eintrag hinzufügen** öffnet das Formular für Ticket, Kunde, Info, Anfang und Ende. **Bearbeiten** an einem abgeschlossenen Arbeitslauf ändert dessen Zeiten und Angaben; die ID bleibt erhalten, Summen werden neu berechnet. Laufende Arbeitsläufe zuerst pausieren oder beenden. Anfang und Ende werden in lokaler Browserzeit eingegeben. Ende muss nach Anfang liegen, darf nicht in der Zukunft liegen und der Zeitraum darf keinen anderen Arbeitslauf überschneiden; direkt angrenzende Zeiten sind erlaubt. Abbrechen speichert nichts. Auch bei Fehlern bleibt das Formular zur Korrektur geöffnet. JSON-/CSV-Datenexport enthält die Arbeitsläufe; der allgemeine Datenimport nimmt diese absichtlich nicht an, damit kein Timer reaktiviert wird. Vollständige Backups sichern die Datenbank einschließlich Timer. Nach Wiederherstellung den laufenden Timer prüfen. Fünf MCP-Werkzeuge sind in docs/MCP_SETUP.md beschrieben.
