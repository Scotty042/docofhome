# DocOfHome 1.7.2

Version 1.7.2 korrigiert die Modellierung und Verkabelung von Neutralleiter- und
Schutzleiterschienen in strukturierten Verteilungen.

## N- und PE-Schienen als Topologie-Endpunkte

Bereiche vom Typ **N-Schiene** und **PE-Schiene** waren bisher nur grafische
Schrankbereiche. Die Topologie konnte ausschließlich echte
`electrical_cabinet_components` als Quelle oder Ziel anbieten. Dadurch waren die
sichtbaren Bereiche im Verbindungsdialog nicht auswählbar.

Ab 1.7.2 gilt:

- ein neu angelegter N-Schienenbereich erzeugt automatisch eine echte
  N-Schrankkomponente mit Leiter `N`;
- ein neu angelegter PE-Schienenbereich erzeugt automatisch eine echte
  PE-Schrankkomponente mit Leiter `PE`;
- Migration `0049` ergänzt diese Komponenten für bereits vorhandene aktive
  N-/PE-Bereiche;
- die Komponenten erscheinen in **Elektro → Versorgungswege** sowohl als Quelle
  als auch als Ziel;
- die Schrankansicht zeigt die Schiene, ihren Verkabelungsstatus und bei
  N-Schienen die optionale FI/RCD-Zuordnung.

## Getrennte Leiterlogik

Reine N- und PE-Verbindungen werden nicht mehr von der Außenleiterlogik
überschrieben:

- FI/RCD → N-Schiene wird als reine N-Verbindung gespeichert;
- N-Schiene → Stromkreis oder DIN-Gerät bleibt ausschließlich N;
- PE-Schiene → Stromkreis oder DIN-Gerät bleibt ausschließlich PE;
- eine vorhandene L1/L2/L3-Versorgung des Zielgeräts blockiert eine zusätzliche
  N- oder PE-Verbindung nicht;
- eine direkte Verbindung zwischen N- und PE-Schiene wird abgelehnt;
- Phasenherkunft und Phasensperre bleiben für reine N-/PE-Verbindungen inaktiv.

## Migration

Alembic-Head: `0049`

Migrationskette:

```text
0045 → 0046 → 0047 → 0048 → 0049
```

Migration `0049` ist datenbewahrend. Beim Downgrade werden erzeugte
Schrankkomponenten bewusst nicht gelöscht, da sie bereits in 1.7.1 gültige
Objekte sind und nach dem Upgrade verkabelt worden sein können.

## Update

1. Persistenten `data`-Ordner sichern.
2. Container mit `docker compose down` stoppen.
3. Version 1.7.2 in einen neuen Ordner entpacken.
4. Image ohne Cache bauen: `docker compose build --no-cache`.
5. Container starten: `docker compose up -d`.
6. Im Log das Upgrade auf Alembic-Head `0049` kontrollieren.
7. Browser mit `Strg+F5` aktualisieren.
8. Unter **Elektro → Versorgungswege** prüfen, ob die vorhandenen N- und
   PE-Schienen angeboten werden.
