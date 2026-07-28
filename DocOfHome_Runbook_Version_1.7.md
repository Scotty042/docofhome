# DocOfHome – Entwicklungs- und Abnahme-Runbook Version 1.7

**Zielversion:** 1.7.0  
**Status:** Freigegebener Umsetzungsumfang  
**Grundlage:** gemeldete Korrekturen und Erweiterungen aus Version 1.6.x

## Release-Ziel
Version 1.7 behebt kritische Inkonsistenzen in der Elektro- und Zählerlogik, ergänzt den IP-Abgleich der FRITZ!Box-Integration und verdichtet mehrere Oberflächen. Datenintegrität hat Vorrang vor rein visuellen Änderungen.

## Umfang und Priorität

- **DOH-1701** – Fehlermeldungen und Toasts immer über Dialogen anzeigen (P1 – hoch)
- **DOH-1702** – Schnittstellengeschwindigkeit als feste Auswahl (P2 – mittel)
- **DOH-1703** – Dokumentierte und ausgelesene IP-Adressen abgleichen (P1 – hoch)
- **DOH-1704** – FRITZ!Box-Geräte numerisch nach IP sortieren (P2 – mittel)
- **DOH-1705** – Hostname-Validierung verständlich machen (P2 – mittel)
- **DOH-1706** – Switch-Frontansicht immer zweireihig und numerisch darstellen (P1 – hoch)
- **DOH-1707** – Stromzähler im Zählerschrank platzieren (P0 – kritisch)
- **DOH-1708** – Monatliche Zählerablesung unter Wartung & Aufgaben anzeigen (P1 – hoch)
- **DOH-1709** – Geräteübersicht kompakter gestalten (P2 – mittel)
- **DOH-1710** – Individuelles Bild direkt am Asset hinterlegen (P2 – mittel)
- **DOH-1711** – Stromkreis zwingend einer konkreten Sicherung zuordnen (P0 – kritisch)
- **DOH-1712** – Phase aus realer Verdrahtung ableiten und falsche Kammschienen-Sperre entfernen (P0 – kritisch)

## Verbindliche Grundregeln

- Frontend und Backend verwenden dieselben Validierungsregeln.
- Physische Verbindungen sind bei Elektroobjekten die Quelle der Wahrheit.
- Importierte oder ausgelesene Werte überschreiben dokumentierte Werte niemals ungefragt.
- Bestehende Daten werden migriert oder als nachzuarbeiten markiert; sie dürfen nicht still verloren gehen.
- Jede Änderung erhält automatisierte Tests sowie einen dokumentierten manuellen Abnahmetest.

## DOH-1701 – Fehlermeldungen und Toasts immer über Dialogen anzeigen

**Priorität:** P1 – hoch  
**Bereich:** Globale Oberfläche / Dialoge  
**Typ:** Fehlerkorrektur

**Fehlerbild:** Validierungs- und Fehlermeldungen werden hinter geöffneten Modal-Dialogen gerendert und sind dadurch teilweise oder vollständig verdeckt.

**Zielzustand:** Globale Meldungen sowie feldbezogene Validierung sind jederzeit sichtbar und eindeutig dem fehlerhaften Vorgang zugeordnet.

### Umsetzungsanforderungen
- Toast-/Snackbar-Container über einen globalen Portal-/Overlay-Container direkt unterhalb von body rendern.
- Eine feste Ebenenreihenfolge definieren: Seiteninhalt < Dropdowns < Backdrop < Modal < Toast/Fehlermeldung.
- Feldbezogene Fehler zusätzlich direkt am betroffenen Eingabefeld anzeigen; ein globaler Toast ersetzt keine Feldmarkierung.
- Mehrere Meldungen sauber stapeln und auf mobilen Ansichten nicht abschneiden.
- Die Korrektur global für alle Dialoge umsetzen, nicht nur für „Netzwerkrolle anlegen“.
### Abnahmekriterien
- Eine absichtlich fehlerhafte Eingabe erzeugt eine vollständig lesbare Meldung oberhalb von Modal und Backdrop.
- Das fehlerhafte Feld ist sichtbar markiert und enthält eine verständliche Ursache.
- Die Darstellung funktioniert auf Desktop, Tablet und Mobilansicht.
- Mehrere Meldungen überdecken weder einander noch die Dialogaktionen.

## DOH-1702 – Schnittstellengeschwindigkeit als feste Auswahl

**Priorität:** P2 – mittel  
**Bereich:** Netzwerk / Schnittstellen  
**Typ:** Bedienverbesserung

**Fehlerbild:** Die Geschwindigkeit einer Netzwerkschnittstelle ist ein frei editierbares Zahlenfeld und erlaubt uneinheitliche oder fehlerhafte Werte.

**Zielzustand:** Die Geschwindigkeit wird über ein Dropdown mit den gewünschten Standardwerten gepflegt.

### Umsetzungsanforderungen
- Auswahlwerte: 100 Mbit/s, 1 Gbit/s und 2,5 Gbit/s.
- Intern weiterhin einheitlich in Mbit/s speichern: 100, 1000, 2500.
- Beim Bearbeiten vorhandener Schnittstellen den gespeicherten Wert korrekt vorauswählen.
- Anzeige in Detailansichten und Übersichten einheitlich formatieren.
### Abnahmekriterien
- Es können keine beliebigen Werte über das normale Eingabefeld erfasst werden.
- Die drei Werte werden korrekt gespeichert und nach erneutem Öffnen unverändert angezeigt.
- 1 Gbit/s wird nicht als 1 GB bezeichnet; Einheit und Schreibweise sind konsistent.

## DOH-1703 – Dokumentierte und ausgelesene IP-Adressen abgleichen

**Priorität:** P1 – hoch  
**Bereich:** Netzwerk / FRITZ!Box-Integration  
**Typ:** Neue Funktion und Validierung

**Fehlerbild:** Ein Asset kann über eine identische MAC-Adresse korrekt einem FRITZ!Box-Client zugeordnet sein, obwohl die in DocOfHome dokumentierte IP von der ausgelesenen IP abweicht. Ein Hinweis fehlt.

**Zielzustand:** DocOfHome erkennt und visualisiert Abweichungen, ohne dokumentierte Daten ungefragt zu überschreiben. Zusätzlich entsteht eine zentrale IP-Übersicht.

### Umsetzungsanforderungen
- Zuordnung primär über normalisierte MAC-Adresse durchführen; Trennzeichen und Groß-/Kleinschreibung dürfen den Vergleich nicht beeinflussen.
- Bei identischer MAC und abweichender IPv4-Adresse direkt am Asset eine Warnung „IP-Abweichung erkannt“ anzeigen.
- Dokumentierte IP und ausgelesene IP gleichzeitig darstellen.
- Aktionen anbieten: dokumentierte IP bearbeiten, ausgelesene IP übernehmen, Abweichung bewusst ignorieren.
- Keine automatische Überschreibung der dokumentierten IP.
- Unter „Netzwerk“ einen eigenen Bereich „IP-Adressen“ ergänzen.
- Spalten: Status, Gerät, Schnittstelle, dokumentierte IP, MAC-Adresse, statisch/DHCP, ausgelesene IP, Quelle, zuletzt erkannt.
- Filter: Abweichungen, Konflikte, statisch, DHCP, nicht erkannt, nur erkannt, Quelle.
- Statuswerte mindestens: Übereinstimmung, Abweichung, nicht erkannt, nur erkannt, IP-Konflikt, keine Integration.
### Datenmodell / Backend
- Beobachtete IP, Quelle und Zeitstempel getrennt von der dokumentierten IP speichern.
- Bei mehreren Schnittstellen und mehreren IPs pro Asset den Vergleich je Schnittstelle/Adresszuordnung durchführen.
- Ein Übernahmevorgang muss nachvollziehbar protokolliert werden.
### Abnahmekriterien
- Beispiel: dokumentiert 192.168.178.3, ausgelesen 192.168.178.1, gleiche MAC – sichtbare Warnung und Status „Abweichung“.
- Nach bewusster Korrektur oder Übernahme wechselt der Status zu „Übereinstimmung“.
- Ohne aktive FRITZ!Box-Integration bleibt die IP-Übersicht für dokumentierte Adressen nutzbar.
- Eine identische IP, die gleichzeitig von unterschiedlichen MAC-Adressen gemeldet wird, erscheint als Konflikt.

## DOH-1704 – FRITZ!Box-Geräte numerisch nach IP sortieren

**Priorität:** P2 – mittel  
**Bereich:** Netzwerk / FRITZ!Box  
**Typ:** Bedienverbesserung

**Fehlerbild:** Die Liste der ausgelesenen Geräte ist nicht sinnvoll nach IP-Adresse sortiert beziehungsweise würde bei Textsortierung falsche Reihenfolgen erzeugen.

**Zielzustand:** Standardmäßig steht die kleinste IP oben, insbesondere die .1.

### Umsetzungsanforderungen
- IPv4-Adressen numerisch anhand der vier Oktette sortieren, nicht lexikografisch als Text.
- Standardsortierung aufsteigend nach Adresse.
- Die Spaltenüberschrift „Adresse“ sortierbar machen und die aktive Richtung anzeigen.
- Datensätze ohne gültige IP am Ende anzeigen.
- Sortierung nach Aktualisierung der FRITZ!Box-Daten beibehalten.
### Abnahmekriterien
- 192.168.178.1 steht vor .2, .10, .20 und .100.
- Online- und Offline-Geräte werden nicht in getrennte Sortierblöcke zerlegt.
- Ein erneuter Klick kehrt die Sortierrichtung korrekt um.

## DOH-1705 – Hostname-Validierung verständlich machen

**Priorität:** P2 – mittel  
**Bereich:** Netzwerkprofil  
**Typ:** Validierung und UX

**Fehlerbild:** Ein Hostname wie fritz.repeater_600-1 wird mit der nichtssagenden Meldung „Value error, Invalid hostname“ abgelehnt.

**Zielzustand:** Ungültige Zeichen werden konkret benannt und eine gültige Alternative wird vorgeschlagen.

### Umsetzungsanforderungen
- Unterstriche im technischen Hostnamen weiterhin ablehnen, sofern die bestehende Hostname-Regel beibehalten wird.
- Meldung direkt am Feld: „Unterstriche sind in Hostnamen nicht erlaubt. Verwenden Sie stattdessen einen Bindestrich.“
- Automatischen Vorschlag erzeugen, z. B. fritz.repeater_600-1 → fritz.repeater-600-1.
- Asset-Anzeigename und technischer Hostname müssen unabhängig voneinander bleiben.
- Bei aus der FRITZ!Box übernommenen Namen den sichtbaren Gerätenamen nicht ungefragt verändern.
### Abnahmekriterien
- Das fehlerhafte Zeichen wird nachvollziehbar erklärt und das Feld hervorgehoben.
- fritz.repeater-600-1 lässt sich speichern.
- Die Meldung liegt gemäß DOH-1701 über dem geöffneten Dialog.

## DOH-1706 – Switch-Frontansicht immer zweireihig und numerisch darstellen

**Priorität:** P1 – hoch  
**Bereich:** Netzwerk / Switch-Ansicht  
**Typ:** Darstellungsfehler

**Fehlerbild:** Ports werden alphabetisch sortiert und bei Platzmangel auf drei oder mehr Reihen umgebrochen.

**Zielzustand:** Die Frontansicht entspricht einer physischen zweireihigen Switch-Front und bleibt auch bei kleinen Viewports zweireihig.

### Umsetzungsanforderungen
- Portnummern numerisch sortieren; Port 10 darf nicht direkt nach Port 1 stehen.
- Genau zwei feste Reihen rendern; kein automatischer Umbruch in eine dritte Reihe.
- Bei Platzmangel horizontal scrollen.
- Für übliche Switches Standardlayout oben ungerade Ports (1, 3, …), unten gerade Ports (2, 4, …).
- Abweichende Gerätefronten über ein konfigurierbares Portlayout am Gerätetyp unterstützen.
- SFP-/Uplink-Ports bei Bedarf als separaten Block darstellen.
### Abnahmekriterien
- Ein 48-Port-Switch erscheint exakt in zwei Reihen.
- Die Reihenfolge entspricht dem hinterlegten physischen Portlayout.
- Ein schmales Browserfenster erzeugt horizontales Scrollen, aber keine dritte Reihe.
- Portstatus, Beschriftungen und Verbindungen bleiben sichtbar und korrekt.

## DOH-1707 – Stromzähler im Zählerschrank platzieren

**Priorität:** P0 – kritisch  
**Bereich:** Zählerschrank / Assets  
**Typ:** Funktionsfehler

**Fehlerbild:** Ein in der Auswahl angebotener Stromzähler wird beim Platzieren mit „Direkt platzierbare Assets müssen vom Typ Zähler sein“ abgelehnt.

**Zielzustand:** Alle vorgesehenen Zähler-Untertypen werden konsistent als platzierbare Zähler erkannt.

### Umsetzungsanforderungen
- Frontend-Auswahl und Backend-Validierung müssen dieselbe stabile Typ-/Capability-Logik verwenden.
- Nicht auf den sichtbaren Anzeigenamen „Zähler“ prüfen, sondern auf eine stabile Kategorie oder Capability wie asset_category=meter bzw. is_meter=true.
- Strom-, Wasser-, Gas- und Wärmezähler akzeptieren, sofern sie als Zähler-Asset klassifiziert sind.
- Nur tatsächlich zulässige Assets in der Auswahlliste anbieten.
- Bei ungeeigneten Assets den erkannten Typ konkret in der Meldung nennen.
### Datenmodell / Backend
- Bestehende Zähler-Untertypen bei der Migration beziehungsweise Initialisierung korrekt mit der gemeinsamen Zähler-Capability versehen.
- Platzierungsregeln für Feld und Position weiterhin serverseitig validieren.
### Abnahmekriterien
- Der ausgewählte Stromzähler lässt sich im vorgesehenen Zählerfeld und an Position 3 platzieren.
- Ein bereits belegter Platz und eine unzulässige Doppelplatzierung werden weiterhin verhindert.
- Bearbeiten und Verschieben eines platzierten Zählers funktionieren.
- Auswahlliste und API liefern für dasselbe Asset kein widersprüchliches Ergebnis.

## DOH-1708 – Monatliche Zählerablesung unter Wartung & Aufgaben anzeigen

**Priorität:** P1 – hoch  
**Bereich:** Wartung & Aufgaben / Verbrauchszähler  
**Typ:** Funktionsfehler

**Fehlerbild:** Eine aktive Ableseregel zum Monatsende erzeugt keinen sichtbaren Hinweis in „Wartung & Aufgaben“.

**Zielzustand:** Aktive Ableseintervalle erzeugen zuverlässig fällige, überfällige und erledigte Aufgaben.

### Umsetzungsanforderungen
- Monatsende kalendarisch korrekt berechnen, einschließlich Februar und 30-Tage-Monaten.
- Aufgabe im bestehenden konfigurierten Vorlauf anzeigen; falls kein Vorlauf existiert, Standardvorlauf von 3 Tagen verwenden.
- Status: bevorstehend, heute fällig, überfällig, erledigt.
- Aufgabe direkt mit dem betroffenen Zähler und der Erfassung des Zählerstands verlinken.
- Eine passende Ablesung für den Fälligkeitszeitraum schließt die Aufgabe automatisch ab.
- Keine Doppelaufgaben pro Zähler und Ableseperiode erzeugen.
- Deaktivierte Regeln erzeugen keine neuen Aufgaben.
### Datenmodell / Backend
- Aufgabeninstanz eindeutig über Zähler-ID plus Fälligkeitsperiode identifizieren.
- Zeitzone und Tagesgrenzen einheitlich behandeln.
- Eine alte Ablesung darf nicht die Aufgabe eines neuen Monats erledigen.
### Abnahmekriterien
- Eine aktive monatliche Ableseregel ist vor dem Monatsende in der zentralen Aufgabenansicht sichtbar.
- Ohne neue Ablesung bleibt sie nach Fälligkeit als überfällig bestehen.
- Eine Ablesung im richtigen Zeitraum erledigt genau die zugehörige Monatsaufgabe.
- Nach Abschluss wird der nächste Monatstermin korrekt geplant.

## DOH-1709 – Geräteübersicht kompakter gestalten

**Priorität:** P2 – mittel  
**Bereich:** Netzwerk / Geräteübersicht  
**Typ:** UX-Optimierung

**Fehlerbild:** Gerätekarten sind sehr hoch, enthalten große Leerflächen und zeigen auf einem Desktop nur wenige Geräte gleichzeitig.

**Zielzustand:** Die Übersicht funktioniert als kompaktes Inventar und zeigt deutlich mehr Geräte ohne Informationsverlust.

### Umsetzungsanforderungen
- Vertikale Innenabstände, Kartenhöhe und Abstände zwischen Informationszeilen reduzieren.
- Gerätename, Rolle und Inventarnummer möglichst in einer kompakten Kopfzeile bündeln.
- Hostname und Standort in einer zweiten kompakten Zeile darstellen.
- Schnittstellen-, IP- und Verbindungsanzahl in einer gemeinsamen Statuszeile zusammenfassen.
- Große Aktionsfußzeile entfernen; Bearbeiten und Archivieren als kleine Icons oder Kontextmenü anbieten.
- Desktop-Raster: bei großer Breite mindestens vier Karten pro Reihe; Tablet zwei; Mobil eine.
- Lange Werte kürzen und den vollständigen Inhalt per Tooltip zugänglich machen.
### Abnahmekriterien
- Auf einem 1920-Pixel-Desktop sind deutlich mehr Geräte ohne Scrollen sichtbar als bisher.
- Karten enthalten keine auffälligen ungenutzten Leerflächen.
- Alle bisherigen Kerndaten und Aktionen bleiben direkt erreichbar.
- Unterschiedlich lange Namen erzeugen weder Überlappung noch unruhige Kartenhöhen.

## DOH-1710 – Individuelles Bild direkt am Asset hinterlegen

**Priorität:** P2 – mittel  
**Bereich:** Assets / Medien  
**Typ:** Neue Funktion

**Fehlerbild:** Bilder können nur am Asset-Typ gepflegt werden; einzelne Assets desselben Typs können nicht mit einem eigenen Foto dokumentiert werden.

**Zielzustand:** Jedes Asset kann ein eigenes Bild erhalten, ohne das gemeinsame Typbild zu verändern.

### Umsetzungsanforderungen
- Im Dialog „Asset anlegen/bearbeiten“ einen Bereich „Bild“ mit Hochladen, Vorschau, Ersetzen und Entfernen ergänzen.
- Fallback-Reihenfolge: individuelles Asset-Bild → Bild des Asset-Typs → Standard-Icon.
- JPEG, PNG und WebP unterstützen; Größenlimit und erlaubte Formate anzeigen.
- Große Bilder serverseitig verkleinern und optimieren.
- Individuelles Bild in Asset-Detail, Asset-Übersicht, Standort-/Raumansicht und relevanten Auswahlansichten verwenden.
- Nur Benutzer mit Bearbeitungsrecht dürfen das Asset-Bild ändern.
### Datenmodell / Backend
- Asset-Bild getrennt vom Asset-Typ-Bild speichern.
- Beim Ersetzen oder Entfernen nicht mehr referenzierte Dateien bereinigen.
- Das Entfernen des Asset-Bildes aktiviert automatisch wieder den Fallback auf das Typbild.
### Abnahmekriterien
- Ein Asset erhält ein eigenes Bild, ohne Bilder anderer Assets desselben Typs zu verändern.
- Nach Entfernen erscheint wieder das Typbild beziehungsweise das Standard-Icon.
- Ungültige oder zu große Dateien erzeugen eine verständliche Meldung.
- Darstellung funktioniert in Desktop- und Mobilansicht.

## DOH-1711 – Stromkreis zwingend einer konkreten Sicherung zuordnen

**Priorität:** P0 – kritisch  
**Bereich:** Elektro / Stromkreise / Verteilung  
**Typ:** Datenintegrität und Pflichtfunktion

**Fehlerbild:** Beim Anlegen oder Bearbeiten eines Stromkreises kann keine konkrete Sicherung ausgewählt werden. Typ und Nennwert allein reichen nicht aus, weil die physische Zuordnung zum Schutzgerät fehlt.

**Zielzustand:** Jeder neue Stromkreis ist zwingend mit dem tatsächlich schützenden Gerät in der Verteilung verknüpft.

### Umsetzungsanforderungen
- Im Stromkreis-Dialog ein Pflichtfeld „Sicherung / Schutzgerät“ ergänzen.
- Nur aktive, platzierte und geeignete Endschutzgeräte aus derselben Verteilung anbieten: Sicherung, Leitungsschutzschalter oder RCBO.
- Ein reiner RCD/FI ohne Überstromschutz darf nicht als Sicherung eines einzelnen Stromkreises ausgewählt werden.
- Auswahleintrag eindeutig beschriften, z. B. „F1.3 – LS B16 A – Position 3 – L2“.
- Nach Auswahl Absicherungstyp und Nennwert automatisch aus dem Schutzgerät übernehmen und nicht widersprüchlich manuell pflegbar lassen.
- Standardmäßig ein Endschutzgerät nur einem Stromkreis zuordnen; mehrpolige Geräte dürfen einen gemeinsamen mehrphasigen Stromkreis schützen.
- Beim Bearbeiten muss die Zuordnung geändert werden können, sofern keine Integritätsregel verletzt wird.
- Archivieren/Löschen eines verknüpften Schutzgeräts nur nach Auflösen oder Übertragen der Stromkreiszuordnung erlauben.
### Datenmodell / Backend
- Stromkreis erhält eine persistente Referenz protective_device_id auf das Schutzgerät.
- Für neue Stromkreise ist die Referenz serverseitig verpflichtend.
- Bestehende Stromkreise ohne Referenz nach Migration als „Zuordnung fehlt“ markieren und in einer Nacharbeitsliste anzeigen, statt die Anwendung zu blockieren.
- Frontend und API verwenden dieselbe Eligibility-Prüfung für auswählbare Schutzgeräte.
### Abnahmekriterien
- Ein neuer Stromkreis kann ohne ausgewählte Sicherung nicht gespeichert werden.
- Nach Auswahl eines LS B16 werden Typ und Wert korrekt übernommen.
- Eine bereits einem anderen einphasigen Stromkreis zugeordnete Sicherung wird nicht erneut angeboten beziehungsweise verständlich als belegt gekennzeichnet.
- Die Stromkreisdetailansicht zeigt die verknüpfte Verteilung, Position und Sicherung.
- Von der Sicherung kann zum Stromkreis und vom Stromkreis zur Sicherung navigiert werden.

## DOH-1712 – Phase aus realer Verdrahtung ableiten und falsche Kammschienen-Sperre entfernen

**Priorität:** P0 – kritisch  
**Bereich:** Elektro / Sicherungen / Stromkreise / Verbindungen  
**Typ:** Datenintegrität und Logikfehler

**Fehlerbild:** Eine per Draht angeschlossene Sicherung wird fälschlich als durch eine Kammschiene versorgt behandelt. Obwohl tatsächlich L2 anliegt, kann zunächst L1 gewählt werden. Später verhindert eine falsche Meldung zur Kammschiene die Korrektur.

**Zielzustand:** Die Phase wird ausschließlich aus der tatsächlichen physischen Verbindung abgeleitet. Veraltete oder nicht existente Kammschienenbezüge dürfen keine Phase sperren.

### Umsetzungsanforderungen
- Quelle der Phase in klarer Priorität bestimmen: aktive Kammschienenverbindung → aktive Drahtverbindung → manuelle Auswahl nur ohne physische Einspeiseverbindung.
- Bei Drahtverbindung die Phase vom tatsächlich verbundenen upstream Anschluss/Leiter übernehmen.
- Liegt am Eingang L2 an, muss L2 automatisch vorausgewählt und mit Hinweis „aus Drahtverbindung übernommen“ dargestellt werden.
- Eine manuelle Auswahl einer widersprüchlichen Phase darf weder im Frontend noch über die API gespeichert werden.
- Die Meldung „von der Kammschiene vorgeschrieben“ nur anzeigen, wenn eine aktive, reale Kammschienenverbindung für genau dieses Gerät und diesen Pol existiert.
- Beim Wechsel von Kammschiene auf Draht oder beim Löschen einer Schienenverbindung alle veralteten busbar_id-, Slot- und Phase-Lock-Daten entfernen und neu berechnen.
- Bestehende falsche Phasenwerte müssen nach Korrektur der Verbindung auf die reale Phase geändert werden können.
- Bei mehrpoligen Schutzgeräten die komplette Phasenmenge L1/L2/L3 aus den jeweiligen Anschlüssen ableiten.
### Datenmodell / Backend
- Phase nicht als unabhängigen, dauerhaft gesperrten Freitext behandeln, sondern mit phase_source und source_connection_id nachvollziehbar machen.
- Migration/Repair-Job: Datensätze mit phase_source=busbar, aber ohne aktive Schienenverbindung finden, Sperre entfernen und Phase aus der Verdrahtung neu berechnen.
- Inkonsistenzen protokollieren und in einer administrativen Prüf-/Nacharbeitsliste anzeigen.
- Backend ist die letzte Autorität; reine UI-Sperren reichen nicht aus.
### Abnahmekriterien
- Testszenario: Sicherung ist per Draht mit L2 verbunden. Der Stromkreis zeigt automatisch L2; L1 kann nicht gespeichert werden.
- Es erscheint keine Kammschienenmeldung, solange keine reale Kammschienenverbindung existiert.
- Ein zuvor falsch gespeicherter Wert L1 kann auf L2 korrigiert werden.
- Nach tatsächlicher Verbindung mit einer Kammschiene wird die Phase korrekt aus Schienenmuster und Position abgeleitet und nachvollziehbar gesperrt.
- Nach Entfernen der Kammschiene entfällt die Sperre sofort und die Draht-/manuelle Logik greift.
### Regressionstests
- N- und PE-Verbindungen bleiben von der Phasenlogik unberührt.
- FI/RCD-Zuordnungen und mehrpolige Geräte behalten ihre korrekte Polzuordnung.
- Bestehende korrekt modellierte Kammschienen werden nicht verändert.

## Empfohlene Umsetzungsreihenfolge

1. Datenmodell und Migration für DOH-1711 und DOH-1712.
1. Backend-Validierung und Repair-Job für Elektro- und Zählerlogik.
1. Frontend für Stromkreis-/Sicherungszuordnung und Phasenherkunft.
1. DOH-1707 und DOH-1708 für Zählerplatzierung und Aufgaben.
1. Netzwerkfunktionen DOH-1703, DOH-1704, DOH-1705 und DOH-1706.
1. Globale Dialogkorrektur DOH-1701 sowie UI-Verdichtung DOH-1702, DOH-1709 und DOH-1710.
1. Vollständige Regression, Migrationsprobe und Release-Abnahme.

## Release- und Deployment-Runbook

- Aktuellen produktiven Datenbankstand und Medienordner sichern.
- Aktuelles 1.6.x-Image beziehungsweise Git-Tag als Rollback-Stand festhalten.
- Migration zunächst gegen eine Kopie produktionsnaher Daten ausführen.
- Repair-Bericht für Phasen-/Kammschieneninkonsistenzen und Stromkreise ohne Sicherung prüfen.
- Automatisierte Tests und die unten genannten Smoke-Tests durchführen.
- Release als 1.7.0 bauen, Versionsanzeige und Changelog aktualisieren.
- Nach Deployment Datenbankmigration ausführen und Anwendungslogs auf Validierungs- oder Integritätsfehler prüfen.
- Bei kritischem Fehler auf 1.6.x zurückrollen und Datenbank-/Medienbackup wiederherstellen; keine teilweise rückgerollte Schema-Version betreiben.

## Pflicht-Smoke-Tests vor Freigabe

- Modal öffnen, ungültigen Wert speichern: Toast sichtbar oberhalb des Dialogs.
- Schnittstelle mit 100, 1000 und 2500 Mbit/s speichern und erneut öffnen.
- FRITZ!Box-Client mit gleicher MAC, aber abweichender IP: Warnung und IP-Übersicht prüfen.
- FRITZ!Box-Liste: .1 muss oben stehen.
- 48-Port-Switch bei schmalem Fenster: exakt zwei Reihen und horizontaler Scrollbalken.
- Stromzähler in Zählerfeld platzieren.
- Monatsend-Ableseaufgabe erzeugen, überfällig werden lassen und durch passende Ablesung erledigen.
- Stromkreis ohne Sicherung speichern: muss blockiert werden; mit Sicherung: muss funktionieren.
- Drahtverbindung auf L2: Stromkreis/Sicherung zeigt L2 und keine Kammschienen-Sperre.
- Asset-Bild hochladen, ersetzen und entfernen; Fallback auf Typbild prüfen.

## Definition of Done

- Alle P0- und P1-Punkte vollständig umgesetzt und abgenommen.
- Keine offenen Datenintegritätsfehler in den Repair-/Migrationsberichten.
- Alle Abnahmekriterien der zwölf Arbeitspakete erfüllt.
- Keine Regression in bestehenden Netzwerk-, Zähler-, Wartungs- und Elektroansichten.
- Changelog nennt alle sichtbaren Änderungen und notwendige Nacharbeiten bestehender Daten.
- Release-Artefakt trägt eindeutig Version 1.7.0.