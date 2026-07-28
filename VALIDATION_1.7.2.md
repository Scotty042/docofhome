# Validierung DocOfHome 1.7.2

## Prüfumfang

- Materialisierung bestehender N-/PE-Bereiche durch Migration `0049`;
- automatische Erzeugung bei neuen Schienenbereichen;
- Auswahl als Quelle und Ziel in der elektrischen Topologie;
- reine N-Verbindungen ohne erzwungene L1/L2/L3-Phase;
- reine PE-Verbindungen ohne erzwungene L1/L2/L3-Phase;
- Ablehnung einer direkten N-zu-PE-Schienenverbindung;
- unveränderte Phasen-/Kammschienenlogik für L1/L2/L3;
- Version und Alembic-Head `0049`.

## Automatisierte Verträge

- Python-Syntaxprüfung für Backend und Migrationen;
- statische Vue-/TypeScript-Syntaxprüfung;
- Releasevertrag `scripts/check-release-1.7.2.py`;
- Migrationstest `scripts/check-migration-0049.py`;
- Backend-Integrationstests für Schienenbereiche und N-/PE-Verbindungen;
- Frontend-Vertragstests für Schienenanlage und Leiterbeschränkung.

## Manuelle Smoke-Tests

1. Bestehende Installation von 1.7.1 auf 1.7.2 aktualisieren.
2. Einen vorhandenen N-Schienenbereich in **Versorgungswege** als Ziel auswählen.
3. FI/RCD → N-Schiene speichern; Ergebnis muss ausschließlich `N` enthalten.
4. N-Schiene → Stromkreis speichern; Ergebnis muss ausschließlich `N` enthalten.
5. PE-Schiene als Quelle auswählen und PE → Stromkreis speichern.
6. Prüfen, dass eine bestehende L1/L2/L3-Zuleitung am Stromkreis erhalten bleibt.
7. N-Schiene → PE-Schiene versuchen; Speichern muss mit verständlicher Meldung
   blockiert werden.

## In dieser Erstellungsumgebung ausgeführt

Erfolgreich ausgeführt wurden:

- Versions-, Branding-, Sammelfix-, Ablese-, Elektrointegritäts- und
  Phasenschienenverträge;
- Python-Kompilierung von Backend, Migrationen und Prüfscripten;
- statische Syntaxprüfung von 182 Vue-/TypeScript-Einheiten;
- isolierte Migrationsprüfungen der Revisionen `0030` bis `0049`;
- Upgrade- und Idempotenzprüfung der neuen Migration `0049`.

Der vollständige Backend-Pytest-Lauf war in dieser Umgebung nicht ausführbar,
weil das erforderliche Paket `sqlmodel` im verfügbaren Python-Paketspiegel nicht
bereitgestellt wurde. Der vollständige Frontend-Build konnte ebenfalls nicht
abgeschlossen werden, da die NPM-Abhängigkeitsinstallation am Paketspiegel
hängen blieb. Die dafür vorgesehenen Tests und Build-Schritte bleiben Bestandteil
von `scripts/check.sh` und müssen beim Docker-Build beziehungsweise in CI laufen.
