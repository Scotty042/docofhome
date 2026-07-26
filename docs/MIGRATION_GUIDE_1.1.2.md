# Migration auf DocOfHome 1.1.2

DocOfHome 1.1.2 führt die Alembic-Revision
`0028_collected_integration_fixes` ein. Die Migration ist additiv und erhält
vorhandene Assets, Zähler, Ablesungen, Schrankbereiche, Elektroverbindungen,
Netzwerkgeräte, Ports und IP-Adressen.

## Vor dem Update

1. In DocOfHome ein lokales Backup erzeugen.
2. Den persistenten `data`-Ordner bei gestopptem Container zusätzlich extern
   sichern.
3. Den bisherigen 1.1.1-Quellstand separat aufbewahren.

## Update

```bash
docker compose down
# Quellstand durch DocOfHome 1.1.2 ersetzen
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Beim Start wird die Datenbank automatisch von Revision `0027` auf `0028`
aktualisiert.

## Was Revision 0028 ergänzt

- Home-Assistant-Entitäten für Live-Leistung und Spannung an
  Verbrauchszählern;
- halbe Schrankbereiche sowie eigene N- und PE-Schienen;
- Zählerplatzierungen für Verbrauchszähler und direkte Assets vom Typ
  **Zähler**;
- den Netzanschluss als erlaubte Quelle elektrischer Verbindungen;
- Mitgliedschaften physischer Ports in logischen Netzwerkschnittstellen.

## Prüfung nach dem Update

- Einen Verbrauchszähler öffnen und Asset, Ort sowie optionale HA-Livewerte
  prüfen.
- Im Zählerschrank ein Zählerfeld sowie zwei halbe Bereiche für N und PE
  anlegen.
- Unter Elektro-Topologie den Netzanschluss als Quelle auswählen.
- Bei einem Router oder Repeater eine virtuelle LAN-Bridge anlegen, physische
  Ports zuordnen und die Geräte-IP an der Bridge hinterlegen.
- Bei einem Switch kontrollieren, dass freie Ports neutral als **Frei** gelten
  und keine Einzelport-Warnungen erzeugen.

## Downgrade-Hinweis

Ein technischer Downgrade auf `0027` ist möglich. Dabei werden die mit 1.1.2
neu angelegten Zählerplatzierungen entfernt, Netzanschluss-Verbindungen gelöscht
und N-/PE-Schienen in generische Anschlussfelder zurückgeführt. Vor einem
Downgrade deshalb zwingend ein Backup anlegen.
