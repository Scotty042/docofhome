# Implementation Summary 1.7.4.9

## Datenmodell

- `WorkSubject` als eigenständige, wiederverwendbare Zuordnung außerhalb des Asset-Inventars;
- optionale `subject_id`-Zuordnung an `WorkItem` bei vollständiger Rückwärtskompatibilität zu bestehenden `target_type`/`target_id`-Verknüpfungen;
- `WorkItemEvent.occurred_at` als fachliches Durchführungsdatum;
- optionale Kosten-, Währungs-, Messwert- und Einheitsfelder;
- `WorkItemEventAttachment` mit Dateiinhalt als BLOB für backup-sichere Anhänge.

## API und Service

- CRUD für Bezugsobjekte;
- Historie lesen, rückwirkend anlegen, bearbeiten und löschen;
- Statistikberechnung aus chronologisch sortierten Durchführungen;
- Upload, Download und Löschen von Historienanhängen;
- bestehendes `complete` erzeugt weiterhin den Statusübergang und zusätzlich den detaillierten Historieneintrag;
- wiederkehrende Tagesintervalle verwenden das tatsächliche Durchführungsdatum als Basis für den nächsten Termin.

## Oberfläche

- Bezugsobjekte direkt unter „Wartung & Aufgaben“ verwalten und filtern;
- Tätigkeiten einem Bezugsobjekt zuordnen;
- eigener Historien-Dialog mit Kennzahlen und Zeitleiste;
- vergangene Durchführung nachtragen beziehungsweise bearbeiten;
- Kosten, Messwert und Anhang je Durchführung erfassen;
- bestehende objektgebundene Wartungen bleiben weiterhin nutzbar.
