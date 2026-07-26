# Migration auf DocOfHome 1.3.1

## Voraussetzungen

- vollständiges DocOfHome-Backup aus der Oberfläche;
- zusätzliche externe Sicherung des persistenten `data`-Ordners;
- funktionierender Stand 1.3.0 oder ein älterer vollständig migrierbarer Stand.

## Update

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=200
```

Beim Containerstart führt Alembic die Migrationen bis Revision `0032` aus.

## Migration 0032

Die Migration ergänzt die nullable Spalte `module_width` in `asset_types` und
`assets`. Werte müssen, sofern gesetzt, zwischen 1 und 100 TE liegen. Bestehende
Assets und Typen werden nicht verändert und bleiben mit `NULL` gültig.

Nach dem Update kann eine Standardbreite beim Asset-Typ oder eine abweichende
Breite direkt am Asset gepflegt werden. Ein bestehendes DIN-Produkt bleibt als
alternative Quelle der Breite erhalten. Auch Schutzgeräte übernehmen diese
wirksame Breite automatisch bei Anlage, Positionsdialog und Drag-and-drop.

## Empfohlene Prüfung nach dem Update

1. Beim Asset-Typ **Smart Meter** eine Standardbreite von beispielsweise 4 TE
   hinterlegen oder die Breite direkt am Smart-Meter-Asset pflegen.
2. Bei einem Asset-Typ wie **Sicherungsautomat** oder **FI-Schalter** die
   Standardbreite pflegen und prüfen, dass das Schutzgerät sie automatisch
   übernimmt.
3. Die Schrankaufteilung öffnen und prüfen, dass das Asset innerhalb des
   TE-Rasters erscheint.
4. Das Asset auf einer Desktop-Ansicht per Drag-and-drop verschieben.
5. Zwei Einspeisungen zu einem Phasenverteilerblock anlegen und die Anzeige der
   beiden Verbindungen prüfen.
6. Versuchen, einen nicht eingespeisten Leiter als Abgang zu verwenden; die
   API muss dies kontrolliert mit HTTP 422 ablehnen.
7. Den aktuellen Verbrauchsmonat nach einer heutigen Ablesung prüfen.

## Downgrade

Ein Downgrade auf `0031` entfernt ausschließlich die neuen DIN-Breitenfelder an
Assets und Asset-Typen. Vor dem Downgrade müssen diese Werte gesichert werden,
da sie dabei verloren gehen. Bestehende Produktbreiten und gespeicherte
DIN-Platzierungen aus 1.3.0 bleiben davon unberührt.
