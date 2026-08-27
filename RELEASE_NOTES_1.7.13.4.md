# DocOfHome 1.7.13.4

## Vollständige Modul- und Menüsteuerung

- **Bilder** ist jetzt in **Einstellungen → Module und Navigation** verfügbar.
- **Dokumente** ist jetzt separat aktivierbar und im Hauptmenü ein-/ausblendbar.
- **Dienste & Container (Docker)** ist jetzt ebenfalls Bestandteil der Modulübersicht.
- Aktive, aber aus dem Hauptmenü ausgeblendete Einträge erscheinen wie die übrigen Module unter **Sonstiges**.
- Deaktivierte Module sind zusätzlich über ihre direkten Routen nicht mehr aufrufbar.

## Upgrade

Migration `0053` ergänzt die drei bisher fest sichtbaren Bereiche für bestehende Installationen automatisch in `enabled_modules_json` und `main_menu_modules_json`. Dadurch bleibt die bisherige Sichtbarkeit nach dem Update zunächst unverändert und kann anschließend in den Einstellungen angepasst werden.
