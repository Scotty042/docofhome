# DocOfHome 1.7.10

Version 1.7.10 ist das korrigierte Folge-Release zu 1.7.9. Der bereits veröffentlichte
Tag `v1.7.9` bleibt unverändert und reproduzierbar.

## Korrektur

- Unmaskierte Backticks im mehrzeiligen TypeScript-Handbuchtext wurden korrigiert.
- Inline-Code für `read`, `write` und `admin` bleibt als Markdown erhalten.
- Die nginx-Konfiguration wird als einklappbarer Markdown-Codeblock dargestellt.

Alle MCP-Funktionen aus 1.7.9 sind enthalten. Keine Datenbankmigration; Alembic-Head `0052`.
