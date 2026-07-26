# Sprint 0033 – Verbrauchsmodul

**Status:** Implementiert, Betreiberabnahme ausstehend  
**Paketversion:** `0.1.18-dev`  
**Migration:** `0023`

## Ziel

docofhome verwaltet physische Verbrauchszähler, Ablesungen, Monatsauswertungen und die für den
Haushalt festgelegten virtuellen Wasserwerte. Bestehende Daten aus der bisherigen
Verbrauchserfassung können kontrolliert übernommen werden.

## Verbindlicher Umfang

- Zähler für Wasser, Netzstrom, PV-Erzeugung, Gas, Wärme, Heizöl und freie Medien
- optionale Verknüpfung zu Asset, Ort und einer Home-Assistant-Sensorentität
- manuelle Ablesungen mit Zeitpunkt, Notiz, Reset-/Austauschkennzeichen und Quelle
- optionaler Immich-Bildbezug an einer Ablesung
- Plausibilitätswarnungen und Erinnerung an ausstehende Ablesungen
- Monatsstatistik über wählbare Zeiträume
- virtuelle Wasserwerte auf Basis von Monatsverbräuchen:
  - `EG Verbrauch = Dusche + Küche + Zählerraum`
  - Heizraum gehört ausdrücklich nicht zum EG
  - `Restliches Haus = Hauptwasser − EG Verbrauch`
- kontrollierter Import aus der bisherigen `verbrauch.sqlite` und aus CSV
- Vorschau vor dem Import, Duplikaterkennung und optionales Überschreiben
- keine Übernahme von Passwörtern, Tokens oder Integrationszugangsdaten aus Altdaten
- responsive Oberfläche mit Übersicht, Zählern, Ablesungen, Statistik, Import und Einstellungen

## Datenmodell

- `consumption_meters`
- `consumption_readings`
- `consumption_notes`
- `consumption_settings`

Physische Zähler bleiben die führenden Datensätze. Virtuelle Werte werden berechnet und nicht als
manipulierbare Zählerstände gespeichert.

## Abnahme

1. Migration einer bestehenden Kopie bis `0023`.
2. Standardzähler anlegen und Wasserrollen prüfen.
3. Für mindestens zwei Zähler mehrere Ablesungen erfassen.
4. Monatswerte sowie EG- und Resthaus-Berechnung kontrollieren.
5. Reset/Austausch eines Zählers testen.
6. Home-Assistant-Sensorwert übernehmen.
7. Alte SQLite-Datei und CSV zunächst als Vorschau, anschließend testweise importieren.
8. Duplikat- und Überschreibeverhalten prüfen.
9. Container neu starten und Persistenz kontrollieren.
