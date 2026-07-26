# Validierungsbericht – DocOfHome 1.1.1

Stand: 23. Juli 2026

## Umfang

Geprüft wurde das Korrekturrelease für die Ableseerinnerungen unter
**Wartung & Aufgaben** auf Basis des ausgelieferten DocOfHome-1.1.0-ZIP.

## Behobene Ursache

Die API `/api/v1/consumption/reading-reminders` übersprang Zähler ohne
monatlichen Ableseplan vollständig. Dadurch wurde die bereits vorhandene globale
Fälligkeit nach X Tagen nicht in das Wartungsmodul übernommen. Zusätzlich war
die komplette Erinnerungskarte im Frontend bei einer leeren Antwort verborgen.

## Ausgeführte lokale Prüfungen

- Python-Syntaxprüfung der geänderten Backend-, Test- und Prüfscripte;
- dependency-freier Rechentest für Zähler ohne Ablesung, überfällige
  Intervallablesung und noch nicht erreichte Fälligkeit;
- statische Prüfung, dass die Erinnerungskarte dauerhaft sichtbar ist;
- statische Prüfung der rückwärtskompatiblen globalen Intervallregel;
- Versionskonsistenz zwischen `VERSION`, Backend, Frontend und Lockdatei;
- vollständige SHA-256-Prüfung aller Manifestdateien nach erneuter Extraktion;
- Vergleich des Alembic-Heads: unverändert `0027_energy_balance`.

## Ergänzte Regressionstests

- Zähler ohne Monatsplan und mit überfälliger letzter Ablesung erscheint;
- Zähler ohne bisherige Ablesung erscheint sofort;
- noch nicht im gewählten Horizont liegende Intervallablesung erscheint nicht;
- monatlich terminierte Erinnerung verschwindet weiterhin nach einer Ablesung
  im betreffenden Zeitraum.

## Nicht ausführbare Gates

Die ZIP enthält keine installierten Python- oder Node-Abhängigkeiten. Daher
konnten vollständige Läufe von SQLModel/Pytest, Ruff, mypy, Vue-TSC, Vite und
Vitest in der strikt lokalen Umgebung nicht erneut ausgeführt werden. Die
entsprechenden Testquellen sind enthalten; diese Gates bleiben Bestandteil des
normalen Docker-/CI-Builds.
