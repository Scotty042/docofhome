# DocOfHome 1.7.13.1

Patch-Release für 1.7.13. Behebt den TypeScript-Buildfehler im neuen Kochmodus: Die Screen-Wake-Lock-API verwendet nun die nativen DOM-Typen, sodass `vue-tsc --noEmit` nicht mehr an einer inkompatiblen `Navigator`-Erweiterung scheitert.

Das Kochbuch erhält eine neu aufgebaute Rezeptoberfläche mit klar getrennten Ansichten für
Lesen, Bearbeiten und Kochen. Die normale Rezeptansicht bleibt in der DocOfHome-Oberfläche;
nur der Kochmodus wird als ablenkungsfreie Vollbildansicht dargestellt.

## Kochmodus

- Viewportfüllende, für iPad und Touch optimierte Kochansicht ohne DocOfHome-Navigation.
- Im Querformat Zutaten links und Zubereitung rechts; im Hochformat responsive Anordnung untereinander.
- Große Touch-Ziele zum Abhaken von Zutaten und Zubereitungsschritten.
- Portionswahl mit sofortiger Skalierung der Zutatenmengen.
- Optionaler Screen Wake Lock („Bildschirm nicht abschalten“) mit sauberem Browser-Fallback.
- Browser-Vollbild wird, sofern unterstützt, zusätzlich angefordert; die Kochansicht funktioniert auch ohne Fullscreen API.

## Rezeptansicht und Editor

- Lesemodus vom Bearbeiten getrennt und für Desktop sowie iPad neu gestaltet.
- Übersichtliche Rezeptinformationen, Bild, Zeiten, Zutaten und Zubereitungsschritte.
- Zutateneditor nach dem Bedienprinzip moderner Rezeptverwaltungen: Menge, Einheit, Zutat und Notiz in einer Zeile.
- Autocomplete-Vorschläge für vorhandene Zutaten, Kategorien und übliche bzw. bereits verwendete Einheiten.
- Zutaten per Drag-and-drop auf Desktop sowie über Touch-Aktionen auf iPad sortierbar.
- Zubereitungsschritte als größere Karten mit Sortieren- und Löschen-Aktionen.
- Leere Zutaten und Schritte werden vor dem Speichern bereinigt.

Keine Datenbankmigration; Alembic-Head bleibt `0052`.
