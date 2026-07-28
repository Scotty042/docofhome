# DocOfHome 1.7.0 – Validierung

## Durchgeführte Prüfungen

- alle Python-Dateien in Backend, Migrationen und Tests erfolgreich kompiliert;
- Python-AST, `package.json`, `package-lock.json` und `pyproject.toml` erfolgreich geparst;
- TypeScript-Dateien und die TypeScript-Blöcke aller Vue-Komponenten syntaktisch transpiliert;
- Versionsvertrag und statischer Releasevertrag `scripts/check-release-1.7.0.py` erfolgreich;
- Migration `0046` auf einem synthetischen 1.6.x-Schema einschließlich Upgrade und Downgrade ausgeführt;
- vorhandene Tests an die verpflichtende Schutzgerätezuordnung angepasst und neue Regressionstests für 1.7 ergänzt.

## Ergänzte Regressionstests

- Hostname mit Unterstrich wird verständlich abgelehnt; vorgeschlagene Bindestrich-Variante ist gültig.
- Schnittstellengeschwindigkeiten akzeptieren ausschließlich 100, 1000 und 2500 Mbit/s.
- FRITZ!Box-Adressen werden numerisch sortiert und ungültige/leere Adressen zuletzt angezeigt.
- IP-Abweichungen werden über normalisierte MAC-Adressen erkannt, ohne die dokumentierte IP automatisch zu ändern.
- Ein neuer Stromkreis ohne konkretes Schutzgerät wird abgelehnt; belegte Geräte werden gekennzeichnet und nicht doppelt zugeordnet.
- Asset-Typ-Capability `is_meter` und Bild-Fallback vom individuellen Bild zum Typbild werden geprüft.
- Bestehende Topologietests wurden auf platzierte Schutzgeräte angepasst.

## In dieser Build-Umgebung nicht ausführbar

Der vollständige Backend-Testlauf, `ruff`, `mypy`, `npm test` und der produktive Frontend-Build konnten in der bereitgestellten Arbeitsumgebung nicht abgeschlossen werden, weil die benötigten Python- und Node-Abhängigkeiten nicht lokal vorhanden waren und der konfigurierte Paketindex bei Installationsversuchen nicht erreichbar war. Die statischen Prüfungen ersetzen deshalb nicht den Pflicht-Smoke-Test und den vollständigen CI-Lauf vor produktiver Freigabe.

## Vor produktiver Freigabe

1. `scripts/check.sh` in einer Umgebung mit installierten Entwicklungsabhängigkeiten ausführen.
2. Migration `0046` gegen eine Kopie der produktiven Datenbank testen.
3. Die Smoke-Tests aus `DocOfHome_Runbook_Version_1.7.md` vollständig durchführen.
4. Repair-/Nacharbeitsfälle für Stromkreise ohne Sicherung und alte Phasenwerte prüfen.
