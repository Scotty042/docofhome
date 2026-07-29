# DocOfHome 1.7.4.4

Stand: 29.07.2026

Version 1.7.4.4 überarbeitet die Routing-Logik der visuellen Hauptverkabelung im Schaltschrank. Leitungen werden nicht mehr starr an Oberseiten geführt, sondern wählen ihre Anschlusspunkte an Geräten, Sicherungen und Sammelschienen passend zur tatsächlichen Verlaufsrichtung.

## Highlights

- dynamische Portwahl an internen Komponenten: oben bei von oben kommenden Leitungen, unten bei von unten kommenden Leitungen;
- direkte Aufwärtsführung zu oberhalb liegenden Sammel- und Phasenschienen ohne unnötige Schleife nach unten;
- saubere Unterseiten-Anbindung für Leitungen, die ein Gerät oder eine Schiene von unten erreichen;
- freie orthogonale Leitungsführung innerhalb der Schrankdarstellung bleibt erhalten;
- fester Abstand der einzelnen Adern bleibt erhalten;
- einzelne Stromkreise sowie ihre LS-/RCBO-Abgänge bleiben weiterhin ausgeblendet.

## Technik

- keine neue Datenbankmigration;
- Alembic-Head bleibt `0049`.
