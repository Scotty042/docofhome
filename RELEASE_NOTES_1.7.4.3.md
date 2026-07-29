# DocOfHome 1.7.4.3

## Freie Leitungsführung mit sichtbarem Aderabstand

Version 1.7.4.3 nimmt die in 1.7.4.2 eingeführte starre Führung über Feldränder
und obere Trassen zurück. Hauptleitungen dürfen wieder innerhalb der
Schrankdarstellung verlaufen. Dadurch bleiben auch Verbindungen sichtbar, die
bei einer ausschließlichen Obertrassenführung abgeschnitten oder außerhalb des
sichtbaren Bereichs geführt wurden.

- Hauptverbindungen werden wieder mit der freien orthogonalen Grundlogik aus
  Version 1.7.4 geroutet.
- L1, L2, L3, N und PE erhalten auf horizontalen und vertikalen Segmenten einen
  festen Abstand von 8 Pixeln.
- Mehrere Verbindungen am selben Gerät werden an getrennten Anschlusspositionen
  aufgefächert.
- Deckungsgleiche Hauptverbindungen zwischen denselben Komponenten werden als
  gemeinsamer Leitungsweg mit der Vereinigung der Leiter dargestellt.
- Einzelne Stromkreise sowie ihre LS-/RCBO-Abgänge bleiben in der
  Schaltschrankgrafik ausgeblendet.
- Automatische Einzelkontakte einer Kamm-/Sammelschiene werden weiterhin nicht
  mehrfach gezeichnet.
- Topologie und Detailansichten bleiben vollständig und unverändert.

Es ist keine Datenbankmigration erforderlich. Der Alembic-Head bleibt `0049`.
