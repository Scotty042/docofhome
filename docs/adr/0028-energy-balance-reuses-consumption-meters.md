# ADR-0028 – Die Energiebilanz verwendet bestehende Verbrauchszähler

## Status

Accepted

## Kontext

Netzbezug, PV-Erzeugung und Netzeinspeisung sind kumulative Energiemengen und
werden bereits durch das Verbrauchsmodul mit Ablesungen, Import, Plausibilität,
Zeitzone und Monatsgrenzen verarbeitet. Eigene Messwerttabellen für Photovoltaik
würden dieselben physischen Zähler doppelt modellieren und könnten zu
widersprüchlichen Monatswerten führen.

## Entscheidung

Die Energiekonfiguration referenziert je einen aktiven kWh-Zähler der Arten
`electricity_grid`, `electricity_pv` und `electricity_feed_in`. Die
Energiebilanz verwendet die vorhandene periodenbezogene Verbrauchsberechnung.
Sie speichert nur Anschlussstammdaten und technische Komponenten; berechnete
Monatskennzahlen werden bei der Abfrage erzeugt und nicht persistiert.

PV-Quellen, Wechselrichter und Speicher können optional auf ein bestehendes
Asset zeigen. Name, Ort, Bilder, Dokumente und Lebenszyklus bleiben dadurch im
Inventar führend.

## Folgen

- keine doppelte Ablage von Zählerständen;
- bestehende Import-, Ablese- und Plausibilitätslogik gilt auch für die Bilanz;
- fehlende Randablesungen bleiben als unvollständige Zeiträume sichtbar;
- eine spätere Erweiterung um weitere Messflüsse muss als eigener Zählertyp und
  expliziter Formelvertrag erfolgen;
- historische Bilanzwerte können sich fachlich ändern, wenn zugrunde liegende
  Ablesungen korrigiert werden.
