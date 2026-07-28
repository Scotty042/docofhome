# DocOfHome 1.7.3

Version 1.7.3 korrigiert die Bewertung getrennter Einspeisungen an demselben
FI/RCD, Schutzgerät, DIN-Asset oder Stromkreis.

## Behobenes Fehlerbild

Eine fachlich gültige Dokumentation konnte bisher fälschlich als abweichend
markiert werden:

```text
Phasenverteilerblock → FI/RCD: L1, L2, L3
Netzanschluss        → FI/RCD: N
```

DocOfHome zeigte auf der separaten N-Verbindung dennoch die wirksamen Leiter
`L1, L2, L3, N` und meldete eine Abweichung. Ursache war, dass die Anwendung
die aggregierte Gesamtversorgung des Zielgeräts auf jede einzelne Verbindung
übertragen hat.

## Verhalten ab 1.7.3

- jede Verbindung wird anhand ihrer eigenen gespeicherten Leiter bewertet;
- eine N-Verbindung bleibt wirksam ausschließlich `N`;
- eine PE-Verbindung bleibt wirksam ausschließlich `PE`;
- parallele L1/L2/L3-Verbindungen bleiben unverändert;
- die Gesamtversorgung des FI/RCD enthält weiterhin die Vereinigung aller
  eingehenden Leiter, im Beispiel also `L1, L2, L3, N`;
- eine gültige N-/PE-Einzelleiterverbindung erhält keine Phasenwarnung und keine
  Außenleiter-Phasensperre;
- der Verbindungsdialog erweitert eine bewusste N-/PE-Auswahl nicht mehr um die
  Außenleiter eines parallelen Einspeisewegs.

## Datenbank

Alembic-Head: `0049`

Für diese Korrektur ist keine neue Migration erforderlich. Bestehende
Verbindungen werden beim Lesen unmittelbar korrekt bewertet. Ein erneutes
Speichern ist nicht erforderlich.

## Update

1. Persistenten `data`-Ordner sichern.
2. Container mit `docker compose down` stoppen.
3. Version 1.7.3 in einen neuen Ordner entpacken.
4. Image ohne Cache bauen: `docker compose build --no-cache`.
5. Container starten: `docker compose up -d`.
6. Browser mit `Strg+F5` aktualisieren.
7. Unter **Elektro → Versorgungswege** die separate N-Verbindung kontrollieren.
