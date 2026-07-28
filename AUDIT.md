# DocOfHome – aktueller Audit- und Qualitätsstatus

Stand: 28. Juli 2026
Release: 1.7.1
Alembic-Head: `0048`

## Einordnung

1.6.3.8 korrigiert die FI/RCD-Gruppenzuordnung für das seit 1.6.3.7 verbindliche
DIN-Asset-Modell. Das Auswahlfeld an Phasen-/Kammschienen und N-Schienen nutzte
noch ausschließlich historische `electrical_protective_devices`. Daher waren als
DIN-Assets platzierte FI-Schutzschalter nicht auswählbar.

## Integritätsregeln

- aktuelle FI/RCD und FI/LS werden als DIN-Assets derselben Verteilung angeboten;
- historische FI/RCD-Schutzgeräte bleiben rückwärtskompatibel;
- eine Schrankkomponente referenziert entweder einen historischen FI/RCD oder ein
  FI/RCD-Asset, niemals beide;
- nur aktive, platzierte Assets mit passendem FI/RCD-Asset-Typ sind zulässig;
- ein referenziertes FI/RCD-Asset kann erst nach dem Lösen der Zuordnung aus dem
  Verteilerschrank entfernt werden;
- vorhandene Kammschienen- und DIN-Kontaktlogik bleibt unverändert.

## Qualitätsnachweis

Ausgeführt wurden Versions-, Branding-, Elektro-, Kammschienen-, Python- und
TypeScript-/Vue-Syntaxprüfungen sowie sämtliche Migrationsprüfungen bis `0047`.
Der vollständige Pytest-, Ruff-, Mypy-, Vite- und Docker-Lauf benötigt die externen
Projektabhängigkeiten und ist auf dem Zielsystem auszuführen.


## Ergänzung 1.7.1

Der Abgleich gegen 1.7.0 hat einen fachlichen Modellkonflikt aufgelöst:
Stromkreise referenzierten dort ausschließlich historische Schutzgeräte,
während seit 1.6.3.7 neue Geräte als DIN-Assets angelegt werden. 1.7.1
unterstützt beide Referenzarten mit gegenseitigem Ausschluss und serverseitiger
Validierung. Eigenständige FI/RCD bleiben als Gruppen-Schutzgeräte von der
Zuordnung zu einem einzelnen Stromkreis ausgeschlossen.
