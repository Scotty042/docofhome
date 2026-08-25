# Sprint 0024 – Elektrische Versorgungswege

## Status

Lokal implementiert und geprüft.

## Ziel

docofhome dokumentiert den tatsächlichen Versorgungsweg vom Hausanschluss oder einer anderen
Einspeisung über Zähler, Verteilungen und Schutzgeräte bis zu Stromkreisen und Endgeräten. Daraus
werden gemeinsame Einspeisung, ankommende Phasen und nachgelagerte Komponenten abgeleitet.

## Umfang

- vorhandene Assets als Endpunkte für Hausanschluss, Zähler und Endgeräte
- automatische Endpunkte für Verteilungen, Schutzgeräte und Stromkreise
- gerichtete Verbindung „Quelle versorgt Ziel“
- eine aktive Einspeisung pro Ziel und Schutz vor zyklischen Verbindungen
- Leiterbelegung L1, L2, L3, N und PE
- Verbindungsarten Kabel, Einzelader, Sammelschiene, intern oder unbekannt
- optionale Kabeldaten für Typ, Adern, Querschnitt, Länge, Verlauf und Notizen
- responsive Baumansicht mit direkter Navigation zu vorhandenen Datensätzen
- Gruppierung nach Wurzel-Einspeisung
- L1-/L2-/L3-Verbindungsübersicht
- automatische Anzahl nachgelagerter Sicherungen, Stromkreise und End-Assets
- eigene FI-/RCD-Zusammenfassung
- additive Datenbankmigration `0016`

## Abgrenzung

- keine automatische Erzeugung von Verbindungen aus räumlicher Nähe oder bestehenden Zuordnungen
- noch keine Mehrfacheinspeisung, Netzumschaltung, PV-, Batterie- oder Generatorlogik
- noch keine Klemmen- oder adergenaue Anschlussmatrix
- keine Leitungsberechnung, Selektivitätsprüfung oder normgerechte Anlagenprüfung

## Abnahme

- eine vollständige Kette vom Einspeise-Asset bis zum Endgerät lässt sich erfassen und bearbeiten
- Schleifen und eine zweite aktive Einspeisung desselben Ziels werden abgewiesen
- Phasen und Kabeldaten werden vollständig gelesen und geschrieben
- FI-/RCD- sowie Nachfolgerzahlen werden aus der Topologie berechnet
- Migration, Backend, Frontend, Typprüfung und Produktions-Build sind erfolgreich
