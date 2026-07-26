# Sprint 0038 – Photovoltaik und Energiebilanz

**Status:** Completed  
**Paketversion:** `1.1.0`  
**Migration:** `0027`

## Ziel

DocOfHome dokumentiert die lokale Energieinfrastruktur und berechnet aus den
bestehenden kumulativen Zählerständen eine nachvollziehbare monatliche
PV- und Energiebilanz. Netzanschluss, Vertragspartner und technische
Energiekomponenten bleiben mit Inventar und Elektro-Topologie verknüpfbar.

## Verbindlicher Umfang

- eigener Zählertyp `electricity_feed_in` für Netzeinspeisung
- eindeutige, automatisch übertragene Dashboard-Primärzuordnung je Zählerart
  sowie deterministischer Fallback für Strom und Gas
- Statistikdiagramme mit eigener Skalierung je Zähler beziehungsweise Serie
- Ableseerinnerungen im Modul **Wartung & Aufgaben** mit direktem Einstieg in
  die betreffende Ablesung
- visuelle Auswahl eines Zählerfotos aus dem in Immich ausgewählten Album
- Stammdaten für Netzanschluss, Netzbetreiber, Energieversorger,
  Zählpunkt/Marktlokation und Anschlussleistung
- Zuordnung je eines kumulativen kWh-Zählers für Netzbezug, PV-Erzeugung und
  Netzeinspeisung
- beliebig viele PV-Quellen, Wechselrichter und Speicher; optionale Verknüpfung
  zu einem vorhandenen Asset
- mehrere eingehende Energiequellen an einem Ziel der Elektro-Topologie bei
  weiterhin verbotenen Zyklen und doppelten identischen Verbindungen
- monatliche Berechnung von Hausverbrauch, Eigenverbrauch, Autarkiegrad und
  Eigenverbrauchsquote
- Migration, Regressionstests, Release-Dokumentation, Manifest und SHA-256

## Berechnungsvertrag

Für jeden vollständig abgedeckten Monatszeitraum gelten:

```text
Hausverbrauch = Netzbezug + PV-Erzeugung - Netzeinspeisung
Eigenverbrauch = PV-Erzeugung - Netzeinspeisung
Autarkiegrad = Eigenverbrauch / Hausverbrauch * 100
Eigenverbrauchsquote = Eigenverbrauch / PV-Erzeugung * 100
```

Fehlende Randablesungen, Schätzanteile oder physikalisch negative
Zwischenergebnisse werden nicht verborgen. Der Zeitraum wird als unvollständig
markiert; negative Ergebniswerte werden für die Darstellung auf null begrenzt.

## Datenmodell und API

Neue Tabellen:

- `energy_configurations`: singletonartige Anschluss- und Zählerzuordnung
- `energy_components`: PV-Quellen, Wechselrichter und Speicher

Neue API-Routen:

- `GET|PUT /api/v1/energy/configuration`
- `GET|POST /api/v1/energy/components`
- `PUT|DELETE /api/v1/energy/components/{id}`
- `GET /api/v1/energy/balance?months=...`

Die Messwerte verbleiben führend in `consumption_meters` und
`consumption_readings`. Berechnete Bilanzwerte werden nicht als manipulierbare
Zählerstände gespeichert.

## Migration

Migration `0027`:

1. erweitert den Zählertyp-Check um `electricity_feed_in`;
2. entfernt den bisherigen Unique-Index, der nur eine Versorgung pro
   Topologie-Ziel erlaubte;
3. erzeugt Energie-Konfiguration und Energiekomponenten;
4. legt die leere Konfiguration mit ID `1` an.

Bestehende Zähler, Ablesungen, Assets und elektrische Verbindungen werden nicht
umgeschrieben.

## Abnahmekriterien

1. Jeder Statistikblock skaliert ausschließlich mit seinem eigenen Maximum.
2. Wird ein neuer Primärzähler für Strom oder Gas gewählt, verliert der bisherige
   Primärzähler diese Markierung atomar.
3. Ohne Primärmarkierung verwendet das Dashboard den nach Sortierung und Name
   ersten aktiven Zähler der passenden Art.
4. Fällige Ablesungen erscheinen unter **Wartung & Aufgaben** und öffnen den
   richtigen Zähler.
5. Im Ablesedialog können Immich-Vorschaubilder gesucht, ausgewählt und entfernt
   werden; ohne Immich bleibt die manuelle Ablesung nutzbar.
6. Netzbezug, PV-Erzeugung und Netzeinspeisung lassen sich ausschließlich mit
   aktiven kWh-Zählern der passenden Art verbinden.
7. Zwei verschiedene Quellen können dasselbe Topologie-Ziel versorgen; Zyklen
   und identische Doppelverbindungen bleiben verboten.
8. Die Monatsbilanz liefert die vier definierten Kennzahlen und kennzeichnet
   unvollständige Daten.
9. Upgrade `0026 -> 0027`, Downgrade `0027 -> 0026` und erneutes Upgrade laufen
   auf einer lokalen SQLite-Testdatenbank.
10. Release-Versionen, Manifest und SHA-256 sind konsistent.

## Definition of Done

- Backend-, Frontend-, Migrations- und Testquellen sind syntaktisch geprüft.
- Der reale lokale SQLite-Migrationspfad inklusive Datenerhalt ist geprüft.
- Die im Projekt enthaltenen Regressionstests decken Bilanzformeln,
  Mehrquellen-Topologie, Primärzähler und Skalierung ab.
- Release Notes, Changelog, Status, Migrationsanleitung, bekannte Grenzen und
  Validierungsbericht sind auf `1.1.0` aktualisiert.
