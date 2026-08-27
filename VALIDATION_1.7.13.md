# Validierung DocOfHome 1.7.13

- Kochbuch-Leseansicht, Bearbeitungsdialog und Kochmodus technisch getrennt.
- Kochmodus als viewportfüllende Overlay-Ansicht mit responsivem Quer-/Hochformat umgesetzt.
- Screen Wake Lock wird nur bei Browserunterstützung verwendet und bei Sichtbarkeitswechsel erneut angefordert.
- Vollbild-API ist optional; bei fehlender oder abgelehnter Unterstützung bleibt der Kochmodus vollständig nutzbar.
- Zutaten- und Schrittreihenfolge besitzt neben Desktop-Drag-and-drop explizite Touch-Aktionen.
- Portionsskalierung und Druckansicht bleiben erhalten.
- Rezeptdatenmodell und REST-API unverändert; keine Alembic-Migration erforderlich.
- Versions-, Branding-, Release- und TypeScript/Vue-Syntaxprüfungen wurden erfolgreich ausgeführt.
- `python -m compileall` für Backend, Tests und Release-Skripte wurde erfolgreich ausgeführt.
- Ein vollständiger `npm test`-/`npm run build`-Lauf war in der Erstellungsumgebung nicht möglich, weil die npm-Abhängigkeiten dort nicht vollständig aus dem Cache installiert werden konnten. Dieser CI-Lauf ist vor dem produktiven Deployment weiterhin empfohlen.
