# Migration auf DocOfHome 1.2.4

DocOfHome 1.2.4 führt Alembic-Revision
`0030_enable_subdistribution_sections` oberhalb von `0029` ein.

## Vor dem Update

1. In DocOfHome ein lokales ZIP-Backup erstellen.
2. Den gesamten persistenten `data`-Ordner extern sichern.
3. Den bisherigen Quellstand beziehungsweise das bisherige Image aufbewahren.
4. Sicherstellen, dass genügend freier Speicher für Image-Neubau und Backup
   vorhanden ist.

## Update von 1.2.3

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Beim Start führt DocOfHome die Migration von `0029` auf `0030` automatisch aus.
Danach sollte der Healthcheck geprüft und die Anwendung einmal vollständig
geöffnet werden.

## Inhalt der Migration 0030

Die Migration entfernt die Datenbank-Prüfbedingung
`ck_electrical_distributions_sub_rows_layout`. Dadurch darf eine
Unterverteilung neben `rows` auch `sections` als Aufbau verwenden.

Die Migration verändert keine bestehenden Verteilungen und löscht keine
Schrankbereiche, Geräte, Zähler oder Zuordnungen.

## Downgrade auf 0029

Vor einem Downgrade ist zwingend ein vollständiges Backup erforderlich.
Unterverteilungen im Feld-/Bereichsmodus können im alten Schema nicht direkt
abgebildet werden. Beim Downgrade auf `0029` wird deshalb nur deren
`layout_mode` auf `rows` zurückgesetzt. Die zugehörigen Feld- und Bereichsdaten
bleiben in der Datenbank erhalten und werden nach einem erneuten Upgrade auf
`0030` wieder nutzbar.

```bash
cd backend
alembic downgrade 0029
```

Ein Downgrade des Containers ohne passende Quellversion wird nicht empfohlen.

## Nachkontrolle

- Healthcheck und Backend-Log auf Migrationsexceptions prüfen;
- Netzwerkseite öffnen;
- Haupt- und Unterverteilung jeweils über **Schrankaufteilung** öffnen;
- eine Unterverteilung testweise auf **Felder und Bereiche** umstellen;
- mobile Zählerstandserfassung einschließlich eines Validierungsfehlers prüfen;
- Online-Produktbildsuche testen und einen Treffer lokal übernehmen.
