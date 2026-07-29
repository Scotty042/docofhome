# DocOfHome 1.7.4.6

Stand: 29.07.2026

Version 1.7.4.6 korrigiert den Darstellungsfilter der visuellen Schaltschrankverkabelung. In 1.7.4.5 wurden LS-/MCB-/RCBO-Endpunkte vollständig ausgeblendet. Dadurch fehlten auch gültige manuelle Einspeisungen zu einer Sicherung, obwohl sie in den Details korrekt dokumentiert waren.

## Korrektur

- Eine manuelle Einspeisung zu einem LS, MCB oder RCBO wird wieder dargestellt.
- Nur die Verbindung vom Schutzgerät zum einzelnen Stromkreis wird ausgeblendet.
- Automatische Einzelkontakte einer Kamm-/Sammelschiene bleiben weiterhin ausgeblendet, weil die Schieneneinspeisung bereits je Leiter dargestellt wird.
- Beispiel: **Phasenverteilerblock L1/L2/L3 → Sicherung Waschmaschine · L2** ist sichtbar.
- Der nachgelagerte Zweig **Sicherung Waschmaschine → Stromkreis Waschmaschine** bleibt unsichtbar.

## Technik

- keine neue Datenbankmigration;
- Alembic-Head bleibt `0049`.
