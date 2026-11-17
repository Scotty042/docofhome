# Zeiterfassung

Unter **Alltag → Zeiterfassung** Tätigkeit/Ticketnr und Kundenname nebeneinander eingeben, optional weitere Info ergänzen und **Start** drücken. Unter Einstellungen → Module lässt sich die Zeiterfassung samt Menüeintrag schalten.

- **Pause** schließt den Arbeitslauf ab und gibt den Timer für andere Tickets frei.
- **Ende** schließt den Arbeitslauf als beendet ab und leert nach erfolgreicher Speicherung Tätigkeit/Ticketnr, Kundenname und weitere Info für die nächste Aufgabe. Bei einem Speicherfehler bleiben die Eingaben erhalten. Pause erhält die Eingaben ebenfalls.
- **Tätigkeiten von heute wieder aufnehmen** startet einen weiteren Arbeitslauf mit den zuletzt heute verwendeten Tätigkeitsdaten. Die Liste enthält nur Tätigkeiten mit Arbeitszeit am aktuellen lokalen Kalendertag, unabhängig vom Verlaufsfilter; laufende Arbeitsläufe über Mitternacht zählen dazu. Auch beendete Tickets können erneut aufgenommen werden.
- Es läuft immer höchstens ein Timer gleichzeitig. Beim Wechsel zuerst Pause oder Ende drücken.

Der Verlauf unten zeigt standardmäßig die letzten 30 Kalendertage einschließlich heute, die gesamte Arbeitszeit ohne Pausen sowie Ticketsummen. Alle Arbeitsläufe sind nach lokalen Kalendertagen gruppiert, neuester Tag zuerst. Jede Tagesgruppe hat eine Datumsüberschrift und Tagessumme. Darunter stehen Tätigkeit/Ticketnr, Kunde, Info, Anfang, Ende und Dauer. Arbeitsläufe über Mitternacht erscheinen mit ihrem jeweiligen Tagesanteil; das Tagesende wird als 24:00:00 angezeigt. Bearbeiten öffnet den ursprünglichen vollständigen Arbeitslauf. Die Summen über den gesamten Filterzeitraum bleiben erhalten. Die Schnellauswahl bietet Heute, Gestern, letzte 7/30/90/365 Tage, diesen/letzten Monat und dieses/letztes Jahr. Von und Bis einschließlich erlauben eigene Zeiträume; Aktualisieren lädt die Daten neu. Für die Tagessumme Heute wählen. Arbeitsläufe über Mitternacht werden für die Summen anteilig auf beide lokalen Kalendertage verteilt. Die Anzeige verwendet die Zeitzone des Browsers. Gleiche Ticketnummern werden exakt nach Entfernung führender und nachfolgender Leerzeichen gruppiert.

Der Timer wird in der Datenbank gespeichert und verwendet die Serverzeit. Schließen der Seite oder ein Neustart beendet ihn nicht. Andere geöffnete Ansichten werden spätestens nach 15 Sekunden aktualisiert. Bei einem Verbindungsfehler bleibt der zuletzt bestätigte Timer aktiv; nach Wiederverbindung kann er beendet werden.

Migration **0062** ergänzt die Tabelle und aktiviert das neue Modul bei bestehenden Installationen. Es wurde keine produktive Datenbank geändert. Vor Nutzung den regulären Updateprozess inklusive Migration und Frontend-Build ausführen.

Die aktuelle Fassung ist eine gemeinsame persönliche Zeiterfassung ohne Benutzerzuordnung. **Manuellen Eintrag hinzufügen** öffnet das Formular für Tätigkeit/Ticketnr und Kunde nebeneinander, Info, Anfang und Ende. **Bearbeiten** an einem abgeschlossenen Arbeitslauf ändert dessen Zeiten und Angaben; die ID bleibt erhalten, Summen werden neu berechnet. Laufende Arbeitsläufe zuerst pausieren oder beenden. Anfang und Ende werden in lokaler Browserzeit eingegeben. Ende muss nach Anfang liegen und darf nicht in der Zukunft liegen. Überschneidungen sind für parallele Tätigkeiten erlaubt, sowohl bei manuellen Einträgen als auch bei nachträglichen Änderungen. Jede Tätigkeitsdauer wird einzeln summiert; parallele Zeiten werden mehrfach gezählt. Die Summen entsprechen Tätigkeitszeiten und nicht der überschneidungsfreien Anwesenheitszeit. Abbrechen speichert nichts. Auch bei Fehlern bleibt das Formular zur Korrektur geöffnet. JSON-/CSV-Datenexport enthält die Arbeitsläufe; der allgemeine Datenimport nimmt diese absichtlich nicht an, damit kein Timer reaktiviert wird. Vollständige Backups sichern die Datenbank einschließlich Timer. Nach Wiederherstellung den laufenden Timer prüfen. Sechs MCP-Werkzeuge sind in docs/MCP_SETUP.md beschrieben.


## Arbeitsläufe löschen (ab 1.10.3)

Neben Bearbeiten steht bei abgeschlossenen oder pausierten Arbeitsläufen **Löschen**. Der Bestätigungsdialog zeigt Tätigkeit/Kunde sowie Anfang und Ende. **Abbrechen** erhält alle Daten; **Endgültig löschen** entfernt genau diesen Arbeitslauf. Andere Arbeitsläufe derselben Tätigkeit bleiben erhalten. Bei einem Arbeitslauf über Mitternacht werden alle angezeigten Tagesanteile desselben Arbeitslaufs entfernt. Tages-, Tätigkeits- und Gesamtsummen sowie die heutige Wiederaufnahmeliste werden neu berechnet.

Ein laufender Timer muss vor dem Löschen pausiert oder beendet werden. Es gibt keinen Papierkorb; eine Wiederherstellung ist nur aus einem vorher erstellten vollständigen Backup möglich. Bereits vorhandene Backups werden durch das Löschen nicht verändert.

Über MCP steht `delete_work_interval(interval_id)` mit admin-Berechtigung zur Verfügung.


## Sortierung, Kundengruppen und BCS (ab 1.10.6)

Ein Klick auf eine Spaltenüberschrift sortiert aufsteigend; ein weiterer Klick auf dieselbe Überschrift kehrt die Richtung um. Pfeile zeigen die Auswahl. Sortierbar sind Tätigkeit/Ticketnr, Kundenname/Info, Anfang, Ende, Dauer, Status und BCS. Die Tage bleiben immer getrennt, neuester Tag zuerst. Standard: Anfang absteigend.

Die Checkbox **Nach Kunde gruppieren** schaltet die Kundengruppierung ein oder aus. Die Spaltenüberschriften erscheinen nur einmal pro Tag, auch bei mehreren Kundengruppen. Bei Nach Kunde stehen innerhalb jedes Tages die Kunden mit eigener Kundensumme und darunter ihre einzelnen Arbeitsläufe. Kunden werden alphabetisch angezeigt, die Spaltensortierung gilt innerhalb jeder Kundengruppe. Gleichheit richtet sich nach dem gespeicherten Kundennamen; die Gruppierung ändert keine Daten.

Die Zusammenfassungen unter Gesamtzeit im Zeitraum zeigen jetzt Tätigkeit/Ticketnr, Kundenname und Dauer. Gleiche Tätigkeit/Ticketnr bei verschiedenen Kunden wird separat summiert. Auch die heutige Wiederaufnahmeliste unterscheidet solche Kombinationen.

Die Spalte **BCS** hat pro Arbeitslauf eine Checkbox. Setzen oder Entfernen speichert unmittelbar; bei einem Fehler erscheint eine Meldung und es wird kein erfolgreicher Haken vorgetäuscht. Zeiten, Kunde, Info und Timerstatus bleiben unverändert. BCS ist auch für aktive Timer setzbar. Ein neuer Arbeitslauf beginnt ohne BCS-Haken; bei einem Arbeitslauf über Mitternacht zeigen beide Tagesanteile denselben gespeicherten Status. Änderungen an Zeit oder Info erhalten den Haken. BCS ist eine freie Markierung ohne automatische weitere Aktion.

Migration **0063** ergänzt die BCS-Spalte; vorhandene Zeiten und Modulentscheidungen bleiben erhalten, bestehende Arbeitsläufe starten ohne Haken. Vor dem Update vollständig sichern. Die Migration erfolgt regulär beim Containerstart. Ein Downgrade auf 0062 entfernt die BCS-Markierungen, erhält jedoch die Arbeitszeiten. Vollständige Backups sowie JSON-/CSV-Export enthalten BCS; der allgemeine Datenimport von Arbeitsläufen bleibt gesperrt.


## Monatlicher Export und externer Zugang ab 1.11.0

Optionaler monatlicher CSV-Export unter dem Verlauf, standardmäßig ausgeschaltet. Lokal und auf Wunsch zusätzlich nach Nextcloud. [Exportanleitung](TIME_EXPORTS.md). Für die spätere öffentliche Bereitstellung liegen optionale [SWAG-/Authentik-Vorlagen](SWAG_AUTHENTIK.md) bei; sie werden nicht automatisch aktiviert.
