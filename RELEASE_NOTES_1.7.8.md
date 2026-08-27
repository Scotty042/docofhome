# DocOfHome 1.7.8

Version 1.7.8 verbessert MCP-Zugang, Zwischenablage, Dokumentdarstellung und den Schutz
ungespeicherter Einstellungen. Alle Funktionen aus 1.7.7 bleiben erhalten.

## MCP für weitere Clients

- `/mcp` funktioniert unverändert mit `Authorization: Bearer <token>`.
- `/mcp/<token>` nutzt dieselbe Tokenprüfung, Berechtigung und denselben MCP-Server.
- Die Token-URL wird nur angezeigt, solange der Klartext-Token nach Erzeugung vorliegt.

## Robust kopieren

Kopieraktionen versuchen zuerst `navigator.clipboard.writeText` und verwenden bei fehlenden
Rechten oder unsicherem Kontext ein temporäres Textfeld mit `document.execCommand('copy')`.

## Lesbare Dokumentation

Absätze und Listen erhalten mehr Abstand. `Inline-Code` ist klar hervorgehoben. Mehrzeilige
Codeblöcke besitzen Sprache und Kopierbutton; längere Blöcke sind einklappbar.

```nginx
location ^~ /mcp/ {
    proxy_pass http://docofhome:8000;
}
```

## Einstellungen ohne Datenverlust

Eine sticky Leiste zeigt offene Änderungen und bietet **Verwerfen** sowie **Speichern**.
Interne Navigation, Neuladen, Schließen und Verlassen werden bei offenen Änderungen gewarnt.

Keine Datenbankmigration. Der Alembic-Head bleibt `0052`.
