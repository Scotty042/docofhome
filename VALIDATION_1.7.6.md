# Validierung DocOfHome 1.7.6

Stand: 26.08.2026

## Erfolgreich in der Arbeitsumgebung

- Versionskonsistenz für `VERSION`, Backend, Frontend, Lockfile und `SOURCE_INFO.json`
- Python-Syntaxprüfung von Backend, Tests und Migrationen
- Branding-, gesammelte Regression- und Ableseerinnerungs-Verträge
- Releasevertrag 1.7.6 inklusive Erhalt der 1.7.5- und 1.7.4.9-Daten-/UX-Verträge
- Elektro-Integritäts-, Laufzeit- und Phasenschienen-Verträge
- 185 TypeScript-/Vue-Skripteinheiten über den dependency-freien Syntaxprüfer
- Migrationen 0030–0051; 0050 zusätzlich mit SQLite Upgrade/Backfill/BLOB/Downgrade
- Validierung der öffentlichen MCP-Adresse (`/mcp`, keine Credentials/Query/Fragmente)
- FastAPI/Starlette-Routingprobe: `/mcp` wird ohne Redirect an ein eingebettetes ASGI-App übergeben

## Neu enthaltene Tests

Backendtests decken ab:

- sichere MCP-Defaults (deaktiviert, nur lesen)
- Token-Erzeugung und ausschließlich gehashte Speicherung
- Verbot des Aktivierens ohne Token
- Token-Verifikation sowie `read`/`write`/`admin`-Grenzen

Frontendtests decken die separaten MCP-Einstellungs- und Token-Endpunkte ab.

## Umgebungsgrenze

In dieser isolierten Arbeitsumgebung sind `sqlmodel`, `ruff`, `mypy` und das neue
`mcp`-Python-Paket nicht installiert. Externe Paketdownloads sind per DNS blockiert.
Dadurch konnten der vollständige Backend-Pytest, Ruff/Mypy sowie ein echter Runtime-Aufruf
des MCP-SDK hier nicht ausgeführt werden. Die verwendete MCP-2.0-API wurde gegen die
aktuelle offizielle SDK-Dokumentation geprüft.

Der Docker-Build installiert `mcp>=2.0,<2.1` zusammen mit den übrigen Backend-Abhängigkeiten
und enthält weiterhin den vorhandenen Import-Smoketest `from app.main import app`. Ein normaler
online ausgeführter Docker-/GitHub-Build bricht daher bereits beim Image-Build ab, falls SDK,
FastAPI-Mount oder Backend-Import nicht kompatibel sein sollten.

Der vollständige Vue/Vite-Build konnte ebenfalls nicht erneut ausgeführt werden, weil das
hochgeladene Quell-ZIP erwartungsgemäß kein `node_modules` enthält und die benötigten npm-Pakete
nicht aus dem Netz geladen werden können. Der 1.7.5-Basisstand hatte diesen Build bereits
bestanden; die 1.7.6-Änderung der Oberfläche ist auf die MCP-Einstellungskarte begrenzt.
