# DocOfHome 1.6.3.1 – Kammschienen-Autoverkabelung

Stand: 28. Juli 2026

## Anlass

In realen, über mehrere Versionen aktualisierten Datenbanken konnten Schutzgeräte in der
Schrankansicht sichtbar sein, während die separate Abfrage der automatischen
Kammschienen-Verkabelung dieselben Geräte nicht fand. Das Speichern meldete deshalb
„automatisch mit 0 Schutzgeräten verbunden“.

## Korrektur

Die automatische Verkabelung verwendet nun exakt denselben kanonischen
Schutzgeräte-Repositorypfad wie die Schrank- und Verteilungsansicht. Damit existiert nur
noch eine Definition für ein aktives, sichtbares Schutzgerät.

Beim Anlegen, Ändern oder Öffnen der Topologie gilt:

- Quelle: Phasen-/Kammschiene;
- Ziel: jedes vollständig überdeckte aktive Schutzgerät;
- Phase: automatisch aus Startphase und TE-Position;
- allgemeine DIN-Assets bleiben unverbunden;
- bestehende archivierte Automatikkontakte werden reaktiviert;
- konkurrierende manuelle Eingänge des Schutzgeräts werden ersetzt.

## Datenbank

Keine neue Migration. Alembic-Head bleibt `0044`. Der Laufzeitabgleich repariert bereits
vorhandene Schienen beim Speichern oder beim Öffnen der Topologie.

## Update

Das Image muss ohne Cache neu gebaut und der Browser anschließend hart aktualisiert werden.
