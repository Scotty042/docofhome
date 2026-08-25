# Sprint 0021 – Sichtbare MDI-Icons

## Status

Lokal implementiert und geprüft.

## Ziel

Alle in der Oberfläche referenzierten MDI-Symbole sind in der installierten Icon-Schrift vorhanden
und werden sichtbar dargestellt. Reine Icon-Aktionen behalten ihre verständlichen Mouse-over-Texte.

## Umfang

- fehlendes Symbol für die Bearbeitung einer Geräteposition ersetzen
- nicht vorhandene Schutzgeräte-Symbole in Stammdaten, Archiv und Elektroansichten ersetzen
- sämtliche statisch referenzierten MDI-Namen automatisch gegen die installierte Schrift prüfen
- Icon-Prüfung vor Frontend-Tests und Produktions-Build ausführen

## Abnahme

- keine statisch verwendete MDI-Klasse fehlt in `@mdi/font` 7.4.47
- das Positionssymbol aus dem gemeldeten Screenshot wird sichtbar dargestellt
- Schutzgeräte-Symbole werden in allen betroffenen Ansichten sichtbar dargestellt
- Frontend-Tests, Typprüfung und Produktions-Build sind erfolgreich
