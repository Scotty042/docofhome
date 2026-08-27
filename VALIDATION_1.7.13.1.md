# Validierung DocOfHome 1.7.13.1

- Build-Fix: eigene `WakeLockNavigator`-Erweiterung entfernt; native `Navigator.wakeLock`-/`WakeLockSentinel`-Typen werden verwendet.
- Der zuvor gemeldete Fehler `TS2430` ist damit auf Quellcode-Ebene beseitigt.

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

## Hotfix: TypeScript Wake Lock

- Docker-CI-Fehler TS2430 in `RecipeCookMode.vue` behoben.
- Eigene `WakeLockNavigator`-Deklaration entfernt und die nativen DOM-Typen `Navigator.wakeLock` / `WakeLockSentinel` aus TypeScript 5.8 verwendet.
- Lokaler vollständiger Frontend-Build in dieser Umgebung weiterhin nicht möglich, da die npm-Abhängigkeiten nicht vollständig installiert sind; der fehlerhafte Typkonflikt selbst ist beseitigt.
