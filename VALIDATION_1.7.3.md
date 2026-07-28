# Validierung DocOfHome 1.7.3

## Prüfumfang

- parallele L1/L2/L3- und N-Einspeisung an demselben FI/RCD;
- Verbindungsebene bleibt von der aggregierten Geräteversorgung getrennt;
- keine Abweichungswarnung bei einer gültigen N-only- oder PE-only-Verbindung;
- keine Außenleiter-Phasensperre für reine N-/PE-Wege;
- unveränderte Phasenvererbung für Verbindungen, die tatsächlich L1/L2/L3
  führen;
- Frontend erlaubt N-/PE-only auch bei einem Ziel mit bekannter Außenleiterphase;
- Version 1.7.3 bei unverändertem Alembic-Head `0049`.

## Ergänzte Regressionstests

Der Backend-Test bildet genau den gemeldeten Aufbau ab:

```text
Netzanschluss → Phasenverteilerblock: L1, L2, L3
Phasenverteilerblock → FI/RCD:       L1, L2, L3
Netzanschluss → FI/RCD:              N
```

Erwartet werden:

- N-Verbindung: `phases = [N]`;
- N-Verbindung: `effective_phases = [N]`;
- keine `phase_warnings`;
- keine `locked_line_phases`;
- aggregierte FI/RCD-Einspeisung: `L1, L2, L3, N`.

## In dieser Erstellungsumgebung ausgeführt

Erfolgreich ausgeführt wurden:

- Python-Kompilierung der geänderten Backend- und Testdateien;
- Release- und Versionsvertrag 1.7.3;
- statische Vue-/TypeScript-Syntaxprüfung;
- bestehende statische Elektro-, Phasenschienen- und Migrationsverträge bis
  Alembic-Head `0049`.

Der vollständige Backend-Pytest-Lauf konnte nicht ausgeführt werden, weil
`sqlmodel` im verfügbaren Python-Paketspiegel nicht bereitgestellt wurde. Der
vollständige Frontend-Build benötigt die NPM-Abhängigkeiten und muss beim
Docker-Build beziehungsweise in CI ausgeführt werden.
