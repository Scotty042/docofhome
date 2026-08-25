# DocOfHome 1.7.5

## Bezugsobjekte und Tätigkeiten

- Bezugsobjekte wie Tiere, Geräte, Fahrzeuge oder Räume besitzen ein eigenes Tätigkeiten-Untermenü.
- Tätigkeiten lassen sich ohne separaten initialen Fälligkeitstermin wiederholen.
- Wiederholungen werden als „alle X Tage/Wochen/Monate/Jahre“ erfasst.
- „Heute erledigt“ beziehungsweise bei Tieren „Heute gegeben“ protokolliert ohne zusätzlichen Dialog.
- „Anderes Datum / Details“ ergänzt optional Notiz, Kosten, Messwert und Anhänge.

## Datum und Historie

- Historien zeigen ausschließlich das Datum im Format TT.MM.JJJJ.
- Migration 0051 korrigiert versehentlich zweistellig gespeicherte Jahre (z. B. 0026 zu 2026).
- Sortierung und Abstände verwenden kalendarische Daten statt Uhrzeitdifferenzen.
- Die nächste Fälligkeit entsteht aus letzter tatsächlicher Durchführung plus Intervall.
- Die Historie ist kompakt; standardmäßig bleiben Anzahl und Durchschnitt sichtbar.

## Kompatibilität

- Migration 0050 und sämtliche 1.7.4.9-Daten bleiben erhalten.
- Klassische Aufgaben, technische Wartungen, Bezugsobjekte und Anhänge bleiben kompatibel.
- Ein Downgrade löscht keine Tätigkeits- oder Historiedaten.
