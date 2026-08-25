# DocOfHome 1.7.4.9

Stand: 24.08.2026

Version 1.7.4.9 erweitert **Wartung & Aufgaben** um eine echte Tätigkeits- und
Wartungshistorie. Die Funktion ist bewusst nicht mehr ausschließlich an technische
Assets gebunden.

## Neue Bezugsobjekte

Für Tätigkeiten können wiederverwendbare Bezugsobjekte angelegt werden:

- Gerät
- Tier
- Fahrzeug
- Gebäude
- Raum
- Anlage / Installation
- Allgemein
- Sonstiges

Damit kann beispielsweise **Penny** als Tier geführt werden, ohne Penny als Asset
im technischen Inventar anzulegen. Unter diesem Bezugsobjekt können getrennte
Tätigkeiten wie **Impfung**, **Medikament**, **Entwurmung** oder weitere Vorgänge
angelegt werden.

Bestehende Verknüpfungen von Wartungen zu Assets, Orten, Verteilungen,
Schutzgeräten und Stromkreisen bleiben vollständig erhalten.

## Durchführungshistorie

Jede Aufgabe oder Wartung besitzt eine eigene Historie. Vergangene Durchführungen
können nachträglich ergänzt werden. Pro Durchführung stehen zur Verfügung:

- Durchführungsdatum und Uhrzeit
- Notiz
- Kosten und Währung
- Mess- oder Zählerwert mit Einheit
- Dateianhänge/Bilder bis 20 MB pro Datei

Beim normalen **Als durchgeführt markieren** wird automatisch ein Historieneintrag
erzeugt. Das Durchführungsdatum kann dabei optional abweichend gesetzt werden.

## Intervallauswertung

Aus den Durchführungen berechnet DocOfHome automatisch:

- letzte Durchführung
- vorherige Durchführung
- Tage seit der vorherigen Durchführung
- durchschnittlicher Abstand
- kürzester Abstand
- längster Abstand
- Anzahl der dokumentierten Durchführungen

Die Berechnung erfolgt immer innerhalb derselben Tätigkeit. Eine Medikamentengabe
beeinflusst daher beispielsweise nicht den Abstand zwischen zwei Impfungen.

## Anhänge und Backup

Anhänge werden in Version 1.7.4.9 direkt in der SQLite-Datenbank gespeichert.
Dadurch werden sie zusammen mit der Historie durch das bestehende DocOfHome-
Datenbankbackup erfasst und können nicht durch einen separat fehlenden Upload-
Ordner verwaisen.

## Datenbankmigration

Beim Start wird Migration `0050` ausgeführt. Sie:

- erstellt `work_subjects`;
- ergänzt `work_items.subject_id`;
- erweitert `work_item_events` um Durchführungsdatum, Kosten und Messwert;
- übernimmt für bestehende Events `created_at` als bisheriges Durchführungsdatum;
- erstellt `work_item_event_attachments` für DB-basierte Anhänge.

Vor dem Update wird wie gewohnt ein vollständiges DocOfHome-Backup empfohlen.
