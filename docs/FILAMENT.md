# Filament-Sammlung ab 1.9.0

## Bestand und manuelle Pflege

Unter **Filament → Rolle erfassen** mindestens das Material angeben. Hersteller
(auch SUNLU und andere), Variante, Farbname, Farbe, Shop-Farbcode, Zustand
eingeschweißt/offen, Lagerort, ursprüngliches und verbleibendes Gewicht sind optional.
Freie Materialnamen sind möglich. Nachkaufen und Nachkaufnotiz bilden eine eigene
Liste. Die Übersicht zeigt aktive Rollen und die Summe bekannter Restgewichte;
unbekannte Gewichte werden separat gezählt. 0 bedeutet bekannt leer.

Jede physische Rolle besitzt eine stabile `FIL-…`-Kennung und eine interne ID.
Mehrere Rollen gleicher Farbe sind erlaubt. Eine vorhandene RFID identifiziert
dagegen eine bestimmte Rolle; vor manueller Erfassung oder MCP-Anlage prüfen.
Farbname und Shopcode (z. B. 10502) sind von technischen Cloud-Produktkennungen getrennt.
Bearbeiten ist unabhängig vom Hersteller und von der Bambu-Verbindung möglich.
Ungespeicherte Eingaben lösen beim Verlassen eine Warnung aus.

Suche sowie Hersteller-, Material-, Zustands-, AMS-, Nachkauf- und Archivfilter
lassen sich kombinieren. Farbname, Shopcode, Rollen-ID, RFID und Cloud-ID werden
über das Suchfeld gefunden. Menü ausblenden und Modul deaktivieren sind getrennt
unter **Einstellungen → Module** möglich. Deaktivieren stoppt den automatischen Abgleich.

## Bambu Cloud verbinden

1. Unter **Filament → Einstellungen** die Region global oder China auswählen.
2. Die Bambu-Konto-Adresse und Passwort eingeben und anmelden. Bei angeforderter
   Bestätigung den E-Mail-Code eingeben und erneut anmelden. Alternativ einen
   bereits vorhandenen Access Token verwenden. Weitere Konto-Verifikationsverfahren
   werden nicht automatisiert; ggf. einen vorhandenen Token nutzen.
3. Zunächst manuell synchronisieren und Ergebnis/Warnung prüfen. Automatischen
   Abgleich anschließend bei Bedarf aktivieren, Intervall wählen und speichern.
4. Für AMS die Serienkennungen der Drucker (eine pro Zeile) hinterlegen und
   optional den automatischen MQTT-Status aktivieren.

Home Assistant und LAN-Access-Code sind für diese Verbindung nicht erforderlich.
Passwort und E-Mail-Code werden nicht gespeichert. Token und Kontozuordnung
liegen als geheime Systemeinstellungen im lokalen Datenverzeichnis; sie werden
nicht im Status oder JSON-/CSV-Export ausgegeben. Backups enthalten sie und sind
entsprechend vertraulich zu behandeln. Verbindung trennen entfernt die gespeicherte
Cloud-Anmeldung und deaktiviert den Abgleich, erhält aber den lokalen Bestand.

Die Cloud-Schnittstellen sind nicht als stabile öffentliche API zugesichert.
MFA-Änderungen, abgelaufene Tokens, regionale Abweichungen oder Bambu-Änderungen
können eine erneute Anmeldung oder Anpassung erfordern. Die App zeigt Fehler ohne
geheime Eingabewerte. Eine reale Konto-/Druckerprüfung ist nach der Installation nötig.

## Synchronisierung und Archiv

Cloud-ID und Konto sowie verfügbare RFID bilden die technische Identität.
Cloud-Aktualisierungen übernehmen Restmengen und technische Zuordnungen, erhalten
aber manuelle Bezeichnungen, Shopcode, Zustand, Lagerhinweise, Notizen und Nachkaufmarker.
RFID-Werte aus Nullen sind unbekannt. Fehlende oder negative Restwerte bleiben unbekannt.

Alle Seiten werden eingelesen. Wiederholte Seiten, Fehler nach Teilantworten oder
ein Seitenlimit ergeben eine sichtbare Warnung; kurze Seiten allein beweisen keinen
vollständigen Bestand. Nur bei bestätigter Vollständigkeit wird das Fehlen in der
Cloud markiert. Es löscht niemals die lokale Rolle.

Leere Rollen **archivieren**. Ihre Cloud-ID/RFID bleiben erhalten, sodass ein späterer
Sync sie nicht erneut anlegt. Wiederherstellen ist möglich. **Zusätzlich aus der
Bambu Cloud löschen** ist eine getrennte ausdrückliche Auswahl im Archivdialog
und benötigt eine passende aktuelle Kontoverbindung. Schlägt die Cloud-Löschung
fehl, bleibt die Rolle lokal archiviert und die Warnung sichtbar.

Ein bereinigter JSON-Snapshot lässt sich alternativ importieren:

```json
{"spools":[{"id":"123","filamentVendor":"Bambu Lab","filamentType":"PLA","filamentName":"PLA Basic","color":"008844","RFID":"EINDEUTIGE-ROLLENKENNUNG","netWeight":390,"totalNetWeight":1000}],"complete":false,"account_reference":"offline-import"}
```

Keine Login-Antworten oder Tokens importieren. Wiederholte Imports benötigen
dieselbe `account_reference`; ein Offline-Import hat eine eigene Kontozuordnung
und wird nicht automatisch mit späteren Cloud-Konten zusammengeführt.

## AMS-Ansicht

Die optionale Cloud-MQTT-Verbindung nutzt TLS und liest Statusdaten mehrerer
Drucker. Sie fordert ausschließlich einen aktuellen Status an und steuert keine
Druckaufträge. Anfragen sind auf höchstens eine je fünf Minuten begrenzt.
Die tatsächlichen AMS- und Slotkennungen werden dynamisch angezeigt.

Die automatische Zuordnung erfordert eine exakte bekannte Rollenkennung:
Cloud-RFID entspricht häufig `tray_uuid`, nicht dem kürzeren NFC-`tag_uid`.
Gleiche Farbe oder gleiches Material genügen nicht. Unbekannte Slots können
manuell einer aktiven Rolle zugeordnet werden; ein erkennbarer Kennungswechsel
oder leerer Slot hebt die Bindung auf. Eine manuelle Bindung ohne RFID kann einen
unbemerkten Wechsel gleichartiger Fremdrollen nicht zuverlässig erkennen.

**Zuletzt erkannt** bedeutet AMS-Erkennung, nicht nachgewiesener Druckverbrauch.
Teilmeldungen erhalten nicht mitgelieferte Felder. Ausgebliebene Meldungen beweisen
keine Entnahme; Beobachtungen älter als zehn Minuten sind als alt gekennzeichnet.
Cloud-Mengen und Prozente sind Schätzwerte; unbekannte Werte werden nicht als 0 g behandelt.

## Bilder

Im Editor Bilder manuell auswählen oder bei Bambu-Rollen **Bambu-Store-Bild suchen**
auslösen. Die Funktion liest öffentliche Produktdaten und benötigt eine passende
Variante (z. B. PLA Basic) und eine eindeutige Shop-/Produktkennung. Ein genau
passendes Farbbild wird lokal gespeichert und identische Bilder gemeinsam genutzt.
Fehlt eine eindeutige Zuordnung, bleibt ein symbolischer Farbplatzhalter bzw.
das bisherige Bild erhalten. Andere Hersteller und unbekannte Produktadressen
werden manuell bebildert. Ein Sync startet keine automatische Massen-Bildsuche.

## Phomemo M110: 40 × 30 mm

In den Filament-Einstellungen die vom Smartphone erreichbare DocOfHome-Basisadresse
ohne Unterpfad hinterlegen. Gewünschte Rollen markieren (bis 100), anschließend PDF
oder JPG wählen. Die Adresse muss auch Oberfläche und `/api/v1/filament` erreichen;
ein ausschließlich für `/mcp` freigeschalteter Host reicht für QR und Downloads nicht.
Das PDF enthält eine Seite pro Rolle mit exakt 40 × 30 mm.
Ein JPG hat 472 × 354 Pixel bei 300 dpi; mehrere JPGs werden als ZIP angeboten.

Das Etikett enthält Hersteller, Material/Variante, Farbname, Shopcode, stabile
Rollenkennung und einen QR-Link zur Rolle. Lange Texte werden gekürzt; Restgewicht,
AMS-Platz und Datum stehen nicht auf dauerhaften Etiketten. Im Druckdialog bzw.
in der Phomemo-App **40 × 30 mm, 100 % / tatsächliche Größe** einstellen und die
automatische Seitenanpassung ausschalten. Zuerst ein Probeetikett drucken und
den QR-Code mit dem Smartphone prüfen. Ein physischer M110-Druck wurde lokal
nicht durchgeführt. Sehr lange Basisadressen können für einen lesbaren QR-Code
zu dicht sein und werden mit einer verständlichen Fehlermeldung zurückgewiesen.

## MCP und Datenübernahme

Die vorhandene MCP-Verbindung bietet insgesamt 49 Werkzeuge. Neue Filament-Werkzeuge:

| Werkzeug | Berechtigung | Aufgabe |
| --- | --- | --- |
| `search_filament_spools` | read | Kombinierte Filter, aktive/archivierte/alle Rollen; `has_more` und `next_offset` beachten |
| `get_filament_spool` | read | Alle Rollendetails und technische Zuordnung |
| `save_filament_spool` | write | Neu anlegen oder nur übergebene Felder ändern |
| `archive_filament_spool` | admin | Archivieren bzw. `restore=true`; `delete_cloud=true` nur nach ausdrücklichem Nutzerwunsch |
| `get_filament_status` | read | Abgleichstatus und AMS-Slots ohne Zugangsdaten |
| `sync_filament_inventory` | write | Cloud lesen und lokal aktualisieren, optional `refresh_ams=true` |
| `create_filament_labels` | read | PDF/JPG; Downloadlink gilt 24 Stunden, öffentliche Basisadresse erforderlich |
| `fetch_filament_store_image` | write | Eindeutiges Shop-Farbbild lokal übernehmen, ersetzt ein vorhandenes Bild |

Beispiel: „Suche zuerst nach dieser RFID im gesamten Bestand einschließlich Archiv.
Lege die Rolle nur an, wenn sie fehlt, und markiere sie zum Nachkaufen.“
Neue Rollen brauchen mindestens `data.material`; bei Änderungen `spool_id` mitgeben.
Ein MCP-Client mit zwischengespeicherter Werkzeugliste muss diese nach dem Update
neu laden bzw. die Verbindung neu herstellen. `/mcp` mit Bearer und `/mcp/<token>`
funktionieren weiterhin.

JSON-Export/Import enthält Rollen und Slotdaten, CSV kann Rollendaten übertragen.
Cloud-Zugangsdaten fehlen bewusst. Für lokale Bilder und eine vollständige
Wiederherstellung das vollständige Dateibackup verwenden. Vor 1.9-Update ein Backup
erstellen; Migration 0061 läuft beim Start. Ein Downgrade entfernt die neuen
Filamenttabellen und sollte ausschließlich in einer gesicherten Testkopie erfolgen.
