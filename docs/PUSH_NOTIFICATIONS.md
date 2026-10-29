# Push-Benachrichtigungen ab DocOfHome 1.8.0

Die Konfiguration findest du unter **Einstellungen → Push-Benachrichtigungen**.
Nach dem Update ist automatischer Versand ausgeschaltet. Du kannst Pushover,
ntfy oder beide Dienste gleichzeitig nutzen.

## Was wird gesendet?

Eine tägliche Zusammenfassung der ausgewählten Kategorien:

- **Zähler ablesen**: Die bestehenden monatlichen Ablesepläne oder das eingestellte
  Ableseintervall bestimmen die Fälligkeit. Eine gespeicherte Ablesung im gültigen
  Fenster erledigt die entsprechende Erinnerung. Automatisch daraus erzeugte
  Wartungsaufgaben werden nicht ein zweites Mal in derselben Nachricht aufgeführt.
- **Wartungsarbeiten**: Offene, datierte Wartungen einschließlich überfälliger Einträge.
- **Aufgaben und Termine**: Andere offene Aufgaben mit Datum. Erledigte, abgebrochene,
  archivierte oder undatierte Einträge werden nicht gemeldet.

Der Vorlauf ist zwischen 0 und 31 Tagen einstellbar. Bei 0 werden heute fällige und
überfällige Einträge berücksichtigt. Die Uhrzeit gilt in der unter Einstellungen
festgelegten Zeitzone. DocOfHome prüft jede Minute. Bei Neustart nach der Uhrzeit
wird die aktuelle Tageszusammenfassung nachgeholt, nicht jeder verpasste Tag.
Ohne offene Erinnerungen wird nichts versendet. Offene Einträge können am nächsten
Tag erneut erscheinen; sie werden nicht jede Minute verschickt. Neue Einträge nach
bereits erfolgtem Tagesversand erscheinen in der nächsten Tageszusammenfassung.

Lange Zusammenfassungen werden gekürzt und zeigen die Zahl weiterer Einträge.
Die vollständige Liste bleibt in DocOfHome. Eine optionale öffentliche
DocOfHome-Adresse ergänzt einen Link zur Verbrauchs-, Wartungs- oder Startübersicht.
Die Adresse muss ohne Unterpfad angegeben werden und auf dem Smartphone erreichbar
sein, gegebenenfalls über deinen VPN-Zugang.

## Pushover einrichten

1. In deinem vorhandenen Pushover-Konto eine Anwendung für DocOfHome registrieren.
2. Den **Application API Token** und deinen **User Key** oder **Group Key** kopieren.
3. Unter Push-Benachrichtigungen bei Pushover eintragen. Optional einen Gerätenamen
   angeben; leer bedeutet alle Geräte dieses Benutzers. Bei Gruppen gelten die
   Geräteeinschränkungen des Anbieters.
4. **Testnachricht senden** anklicken und den Empfang auf dem Handy prüfen.
5. Pushover verwenden und automatische Push-Erinnerungen aktivieren, Kategorien,
   Uhrzeit und Vorlauf festlegen, anschließend **Speichern**.

Testen versendet eine echte Nachricht mit den aktuellen Eingaben, speichert aber
keine Konfiguration. Bereits gespeicherte Schlüssel werden bei leeren Eingabefeldern
weiterverwendet. Zum Löschen die entsprechende Entfernen-Option wählen.

Offizielle Referenz: https://pushover.net/api

## ntfy einrichten

1. Eigenen ntfy-Server auf deinem NUC betreiben oder einen vorhandenen Dienst nutzen.
   DocOfHome installiert keinen zusätzlichen ntfy-Container automatisch.
2. Die Serveradresse und ein Topic in DocOfHome eintragen. In der ntfy-App denselben
   Server und dasselbe Topic abonnieren.
3. Für geschützte Topics einen ntfy-Access-Token mit Schreibberechtigung eintragen.
   Token und Topic-Leserecht für das Smartphone separat auf dem ntfy-Server einrichten.
4. Testnachricht senden und anschließend Einstellungen speichern und aktivieren.

Ohne Authentifizierung ist ein unerratbares Topic kein vollständiger Zugriffsschutz.
Verwende für private Erinnerungen Topics mit Lese-/Schreibrechten. HTTPS schützt
Token und Nachrichten bei der Übertragung. HTTP ist für bewusst konfigurierte lokale
Server zulässig, überträgt die Daten aber unverschlüsselt. Für sofortige Benachrichtigungen
auf iOS sind bei selbst gehostetem ntfy zusätzliche Servereinstellungen erforderlich.

Offizielle Referenzen:
- https://docs.ntfy.sh/publish/
- https://docs.ntfy.sh/config/#access-control
- https://docs.ntfy.sh/config/#ios-instant-notifications

## Status, Wiederholung und Grenzen

Die letzten 20 Versandversuche werden auf der Einstellungsseite angezeigt. Der Status
**Angenommen** bedeutet, dass der Push-Dienst die Nachricht angenommen hat. Er bestätigt
weder die Anzeige noch das Lesen auf dem Smartphone.

Der Tagesversand wird pro Dienst und Empfänger dauerhaft vermerkt. Ein Neustart oder
mehrere gleichzeitig laufende Prüfungen lösen keinen erneuten bestätigten Tagesversand
aus. Schlägt ein Dienst fehl, kann der andere unabhängig davon erfolgreich senden.
Fehler werden bei weiterhin offenen Erinnerungen mit 15 Minuten Abstand bis zu dreimal am Tag versucht. Ein abgebrochener
Versand wird nach derselben Wartezeit erneut freigegeben. Bei einem Netzwerkausfall nach
Annahme durch den Anbieter kann dennoch eine Wiederholung auftreten; eine garantierte
einmalige Zustellung über externe HTTP-Dienste ist nicht möglich.

Testnachrichten werden nicht automatisch wiederholt. Der Verlauf wird nach 90 Tagen
bereinigt. Die Oberfläche zeigt sichere Fehlermeldungen, keine Anbieterantworten mit
potenziellen Schlüsseln. Bei 401 Zugangsdaten/Topic-Rechte prüfen, bei 429 das
Anbieterlimit beachten, bei Verbindungsfehlern DNS, Firewall und Serveradresse prüfen.

## Sicherung, Export und Zugangsdaten

Zugangsdaten liegen wie andere Integrationsschlüssel lokal in der Datenbank. Normale
API-Antworten geben nur an, ob ein Schlüssel gespeichert ist. Konfiguration einschließlich
Topic und Schlüssel wird als geheim markiert und aus JSON-/CSV-Datenexporten ausgeschlossen.
Der Versandverlauf ist nur lesbar exportierbar und wird beim Datenimport nicht übernommen.
Bei Datenimport sind daher die Push-Dienste neu zu konfigurieren.

Ein vollständiges Backup sichert Datenbank, Push-Konfiguration und Versandverlauf.
Backups sind nicht verschlüsselt und enthalten damit Zugangsdaten. Sie müssen vertraulich
aufbewahrt werden. Beim Wiederherstellen eines älteren Backups kann ein Versandmarker
zurückgesetzt werden; prüfe die automatische Aktivierung vor dem Start einer Testkopie.

Die Konfiguration bleibt von Änderungen allgemeiner Einstellungen getrennt. Ihre eigene
Speicherleiste zeigt ungespeicherte Änderungen an. Navigation, Browser-Verlassen und
Neuladen fragen bei offenen Änderungen nach.
