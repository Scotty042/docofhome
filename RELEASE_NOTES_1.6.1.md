# DocOfHome 1.6.1 – Korrekturen für Zähler, Elektro und Netzwerk

Veröffentlicht: 27. Juli 2026

DocOfHome 1.6.1 setzt die im Korrektur-Runbook vom 27. Juli 2026 beschriebenen
Anpassungen um. Der Schwerpunkt liegt auf klaren Zählerabläufen, einer
vollständigeren PV-Auswertung und konsistenter technischer Dokumentation.

## Wichtigste Änderungen

- Der Zählerwechsel ist vom normalen Ablesen getrennt. Schlussstand,
  Austauschzeitpunkt, neue Zählernummer und Startstand werden gemeinsam und
  atomar gespeichert.
- Der Ablesedialog zeigt den letzten Stand. Für Netzbezug und Einspeisung werden
  die üblichen OBIS-Kennzahlen 1.8.0 beziehungsweise 2.8.0 erläutert.
- Mehrere PV-Erzeugungszähler können gleichzeitig dashboardrelevant sein; ihre
  Werte werden für Periodenvergleiche zusammengeführt.
- Wikimedia Commons und DuckDuckGo Images lassen sich einzeln aktivieren. Das
  Backend setzt diese Auswahl durch und führt relevante Treffer zusammen.
- Direkte elektrische Verbindungen werden am Asset angezeigt. Abgänge eines
  Phasenverteilers sind nach Phase gruppiert.
- Schutzgeräte werden über eine zentrale Klassifikation erkannt, auch wenn sie
  als allgemeine DIN-Platzierung dokumentiert sind.
- Netzwerkschnittstellen besitzen eine eindeutige primäre Schnittstelle je Gerät.
- Smarte Relais/DIN-Schaltaktoren erhalten passende Stammdaten und
  Home-Assistant-Rollen.

## Datenbank

Alembic-Migration `0038`:

- ergänzt Einstellungen für die beiden Produktbildquellen;
- ergänzt die primäre Netzwerkschnittstelle;
- erweitert zulässige Home-Assistant-Rollen;
- erlaubt mehrere primäre PV-Dashboardzähler;
- legt Standarddaten für **Smartes Relais / DIN-Schaltaktor** und
  **Shelly Pro 1** an.

Bestehende Daten werden nicht ersetzt. Vor dem Update ist wie üblich ein
vollständiges Backup des persistenten `data`-Ordners erforderlich.

## Update von 1.6.0

1. Backup erstellen und `data` zusätzlich extern sichern.
2. Container stoppen.
3. 1.6.1 in einen neuen Ordner entpacken und lokale Konfiguration übernehmen.
4. Images neu bauen und Container starten.
5. Prüfen, dass Migration `0038` erfolgreich ausgeführt wurde.

Das Quellpaket enthält weder Laufzeitdaten noch Zugangsdaten.
