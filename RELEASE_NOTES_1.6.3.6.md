# DocOfHome 1.6.3.6

Diese Korrektur behebt einen HTTP-500-Fehler beim Anlegen von Assets für
Stammdaten, die per Migration angelegt wurden.

## Behoben

Der Asset-Typ **Smartes Relais / DIN-Schaltaktor** wurde zusammen mit dem
Produkt **Shelly Pro 1** bereitgestellt. Dabei fehlte jedoch der zugehörige
Nummernkreis `SRA` in `asset_code_counters`. Beim Anlegen des ersten Geräts
konnte deshalb kein DocOfHome-Code wie `SRA-001` reserviert werden.

## Datenreparatur

Migration `0046_repair_asset_code_counters`:

- ergänzt fehlende Nummernkreise für sämtliche Asset-Typen;
- ermittelt die höchste bereits verwendete Nummer aus den vorhandenen
  `jarvis_code`-Werten;
- setzt einen vorhandenen, aber zu niedrigen Zähler auf die nächste freie Nummer;
- verändert keine bestehenden Asset-Codes.

Die Laufzeitlogik besitzt zusätzlich einen selbstheilenden Fallback: Fehlt trotz
Migration ein Zähler, wird er beim nächsten Anlegen eines Assets aus den bereits
vergebenen Codes rekonstruiert.
