# Migration auf DocOfHome 1.2.0

DocOfHome 1.2.0 führt Alembic-Revision `0029` oberhalb von `0028` ein.

## Vor dem Update

1. In DocOfHome ein lokales Backup erstellen.
2. Den vollständigen persistenten `data`-Ordner bei gestopptem Container extern kopieren.
3. Den bisherigen 1.1.3-Quellstand separat aufbewahren.

## Update

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Der Container führt beim Start `alembic upgrade head` aus.

## Migration 0029

- ergänzt Produktbildquelle, Bildreferenz, DIN-Bauform und TE-Breite;
- ergänzt Rollen an vorhandenen HA-Zuordnungen, Standard `additional`;
- ergänzt die Seite `left`/`right` bei halben Schrankbereichen;
- übernimmt bestehende halbe Bereiche als `left`;
- ersetzt die alte eindeutige Ebene durch Regeln für volle Bereiche und halbe Seiten;
- legt die additive Tabelle für allgemeine DIN-Asset-Platzierungen an;
- ergänzt die standardmäßig deaktivierte Online-Produktbildsuche.

## Nachkontrolle

- Home-Assistant-Seite, Suche und Seitenwechsel öffnen;
- bestehende HA-Zuordnungen an mindestens einem Asset prüfen;
- vorhandene Zählerschränke und N-/PE-Bereiche kontrollieren;
- ein DIN-Produkt mit TE-Breite testweise platzieren;
- vorhandene Produktbilder, Zähler, Verkabelungen und Labels stichprobenartig prüfen.

## Downgrade

`alembic downgrade 0028` entfernt neue DIN-Asset-Platzierungen, Rollen und
Felder. Liegen zwei halbe Bereiche auf derselben Ebene, verschiebt der Downgrade
einen Bereich auf eine freie Ebene, statt ihn zu löschen. Ein Downgrade sollte
nur nach vollständigem Backup erfolgen.
