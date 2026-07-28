# DocOfHome 1.6.3 – Elektro-Integrität und Beziehungslogik

Veröffentlicht: 27. Juli 2026

DocOfHome 1.6.3 baut auf 1.6.2 auf und überprüft das Elektro-Modul als
zusammenhängendes System. Dabei wurden nicht nur einzelne Dialogfehler, sondern
die Beziehungen zwischen Platzierung, automatischer Verkabelung, Topologie,
Stromkreisen, Messpunkten und Archivierung vereinheitlicht.

## Wichtigste Korrekturen

### Phasen-/Kammschienen

- Eine Phasen-/Kammschiene erzeugt automatisch genau eine schreibgeschützte
  Verbindung zu jedem vollständig überdeckten Schutzgerät.
- Neue, verschobene oder technisch geänderte Schutzgeräte synchronisieren ihre
  Schienenverbindung und Außenleiterphase automatisch.
- Teilüberdeckungen, mehrere gleichzeitig phasenbestimmende Schienen und
  Phasenschienen über beliebigen DIN-Assets werden abgewiesen.
- Die optionale FI/RCD-Zuordnung ist keine Voraussetzung für eine Kammschiene.
- Eine legitime Einspeisung **FI/RCD → Phasenschiene** bleibt erhalten und wird
  nicht mit den automatisch verwalteten Ausgängen verwechselt.
- Manuelle Verbindungen allgemeiner Sammelschienen werden nicht mehr als
  Kammschienen-Automatik archiviert oder umgeschrieben.

### Wirksame Phasen und Topologie

- Die Außenleiterphase wird zentral aus Startphase, TE-Position, Gerätetyp und
  Polzahl berechnet.
- Automatische Kammschienen-Verbindungen können weder bearbeitet noch gelöscht
  werden; Änderungen erfolgen über Schiene oder Geräteplatzierung.
- Nachgelagerte Verbindungen eines phasenbestimmten Schutzgeräts werden auf die
  wirksame Außenleiterphase synchronisiert; N und PE bleiben erhalten.
- Stromkreise übernehmen ihre wirksame Phase aus Schutzgerät oder dokumentierter
  Einspeisung und geben sie verbindlich an Verbraucher weiter.
- Topologie und Bearbeitungsdialog verwenden die serverseitig berechneten
  gesperrten Phasen statt historischer manueller Werte.
- Fehlende oder unvollständige Einspeisungen von Schrankkomponenten werden als
  nachvollziehbare Warnung angezeigt.

### FI-, N- und PE-Beziehungen

- FI/RCD-Verknüpfungen sind nur an Phasenschienen und N-Schienen zulässig.
- Eine N-Schiene kann nicht archiviert oder in einen anderen Typ umgewandelt
  werden, solange Schutzgeräte sie verwenden.
- Widersprüche zwischen manueller FI-Zuordnung, Kammschiene und N-Schiene werden
  validiert.
- FI/LS-Geräte (RCBO) erzeugen keine falsche Warnung wegen einer fehlenden
  separaten N-Schiene.

### Smart Meter und Messpunkte

- Ein Messpunkt kann nur L1/L2/L3/N auswählen, wenn dieser Leiter auf der
  wirksamen Verbindung vorhanden ist.
- Bei genau einer wirksamen Außenleiterphase wird sie automatisch übernommen.
- Beim Reparieren oder Ersetzen automatischer Schienenverbindungen bleiben
  Messpunkte erhalten und werden auf die autoritative Verbindung umgehängt.

### Lebenszyklus und Archivierung

- Schutzgeräte mit manuellen aktiven Verbindungen können nicht archiviert
  werden; nur die automatisch abgeleitete Kammschienen-Verbindung wird intern
  verwaltet.
- Stromkreise mit aktiven Topologieverbindungen können nicht archiviert werden.
- Allgemeine Assets können nicht archiviert, ersetzt oder an einen anderen Ort
  verschoben werden, solange aktive elektrische Verbindungen auf sie zeigen.
- Layoutwechsel und Komponententypwechsel prüfen nun alle abhängigen
  Platzierungen und Beziehungen.

## Migration 0043

Migration `0043_release_1_6_3_electrical_integrity`:

- normalisiert Leiter und FI-Verweise an Phasen-, N- und PE-Schienen;
- repariert eindeutige automatische Phasenschienen-Verbindungen;
- bewahrt legitime vorgelagerte FI/RCD-Einspeisungen;
- korrigiert nachgelagerte Außenleiter und Smart-Meter-Messphasen;
- ergänzt Datenbank-Constraints für die Schienentypen.

## Update von 1.6.2

1. Persistent gespeicherten `data`-Ordner vollständig sichern.
2. Container stoppen: `docker compose down`.
3. DocOfHome 1.6.3 in einen neuen sauberen Ordner entpacken.
4. Lokale `.env`- und Compose-Anpassungen übernehmen.
5. Neu bauen: `docker compose build --no-cache`.
6. Starten: `docker compose up -d`.
7. Logs prüfen: `docker compose logs -f jarvis`.

Im Log muss das Upgrade `0042 -> 0043` erfolgreich durchlaufen. Anschließend
Browsercache vollständig aktualisieren.

## Hinweis

DocOfHome dokumentiert die bestehende Elektroinstallation. Es ersetzt keine
Planung, Prüfung oder Freigabe durch eine Elektrofachkraft.
## Nachträgliche Build-Korrektur

Der Quellvertragstest für die automatische Phasenschienen-Verkabelung liest die Vue-Datei
nun über Vites `?raw`-Import. Der vorherige Import von `node:fs` war mit dem bewusst
browserorientierten `tsconfig.json` nicht vereinbar und ließ `vue-tsc --noEmit` abbrechen.
Die Laufzeitlogik und die Datenmigration 0043 bleiben unverändert.

## Nachträgliche Korrektur der Schrankansicht und Selbstheilung

- Bereits angelegte Schutzgeräte können innerhalb des Bereichs einer
  Phasen-/Kammschiene wieder per Drag-and-drop verschoben werden. Eine
  Teilüberdeckung bleibt weiterhin unzulässig.
- Allgemeine DIN-Assets wie ein Stromstoßschalter werden klar von Schutzgeräten
  unterschieden. Sie dürfen nicht unter eine Kammschiene gezogen werden und
  erhalten nun eine eindeutige Fehlermeldung.
- Fehlende automatische Verbindungen **Phasenschiene → Schutzgerät** werden beim
  Öffnen der Topologie beziehungsweise der Verbindungsliste selbstheilend
  rekonstruiert. Die Synchronisierung wird vor der Auswertung sicher geflusht
  und ist im stabilen Zustand idempotent.
- In der Detailseitenleiste stehen für Schutzgeräte und Schrankkomponenten
  Archivieren-Schaltflächen zur Verfügung.
- Beim Archivieren einer Phasen-/Kammschiene bleiben die Sicherungen platziert;
  die Einspeisung der Schiene und ihre automatisch abgeleiteten Kontakte werden
  gemeinsam historisch archiviert.

## Nachträgliche Korrektur: gemischte DIN-Reihen und Dialogfehler

- Phasen-/Kammschienen dürfen nun über allgemeinen DIN-Geräten wie Stromstoßschaltern dargestellt werden.
- Solche DIN-Geräte werden ausdrücklich nicht automatisch mit der Kammschiene verkabelt.
- Automatische Schienenkontakte entstehen weiterhin ausschließlich für vollständig überdeckte Schutzgeräte.
- Allgemeine DIN-Geräte können auch nachträglich innerhalb des dargestellten Schienenbereichs platziert oder verschoben werden.
- Die Fehlermeldung des Schrankkomponenten-Dialogs liegt nun im scrollbaren Dialoginhalt und wird nicht mehr hinter den Aktionsschaltflächen abgeschnitten.
