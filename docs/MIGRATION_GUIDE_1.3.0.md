# Migration auf DocOfHome 1.3.0

## Voraussetzungen

- vollständiges DocOfHome-Backup aus der Oberfläche;
- zusätzliche externe Sicherung des persistenten `data`-Ordners;
- funktionierender Stand 1.2.4 oder ein älterer, vollständig migrierbarer Stand.

## Update

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Beim Containerstart führt Alembic die Migrationen bis Revision `0031` aus.

## Migration 0031

Die Migration legt passive Schrankkomponenten an, erweitert die
Verkabelungsendpunkte und erlaubt DIN-Asset-Platzierungen ohne Bereichs-ID in
einer einfachen Reihenaufteilung. Vorhandene Assets, Verteilungen, Bereiche,
Schutzgeräte, Zähler, Netzwerkdaten und Verbindungen werden nicht umgeschrieben.

## Downgrade

Ein Downgrade auf `0030` entfernt Verbindungen zu Schrankkomponenten und die
Schrankkomponenten selbst. DIN-Asset-Platzierungen in einer einfachen
Reihenaufteilung können in Revision 0030 nicht dargestellt werden und werden
vor der Wiederherstellung der Pflicht-Bereichs-ID entfernt. Ein Downgrade darf
deshalb nur nach einem vollständigen Backup und mit bewusst akzeptiertem
Datenverlust dieser neuen 1.3.0-Daten erfolgen.
