# Planungsnotiz – geführter Einrichtungsassistent

> **Vorgesehener Sprint:** 0035  
> **Status:** unverbindliche Ideensammlung; noch kein Sprintvertrag  
> **Voraussetzungen:** Netzwerkmodul, Verbrauchsmodul sowie Import/Export und Änderungshistorie sind fachlich fertig und abgenommen

## Ziel

Der Assistent soll komplexe Hauskomponenten in einem geführten Ablauf vollständig dokumentieren,
ohne dass Benutzer jedes beteiligte Modul einzeln kennen oder in der richtigen Reihenfolge öffnen
müssen. Er orchestriert bestehende APIs und Fachregeln; er führt keine parallelen Schattenmodelle
ein.

## Voraussichtlich einzubeziehende Module

- Bereiche, Räume und Installationspunkte
- Assets, Asset-Typen, Produkte, Labels und Beziehungen
- Elektroverteilungen, Schutzgeräte, Stromkreise, Positionen und Versorgungstopologie
- Home-Assistant-Geräte und -Entitäten
- Immich-Bilder und Fotoverknüpfungen
- Nextcloud-Dokumente und Dokumentverknüpfungen
- Wiki-Seiten und objektbezogene Notizen
- Wartungen, Aufgaben und Erinnerungen
- Netzwerkgeräte, Schnittstellen, Adressen und Verbindungen
- Zähler, Verbrauchsdaten und abgeleitete Gruppen
- Importquellen und Änderungshistorie

## Möglicher geführter Ablauf

1. Art der anzulegenden Komponente oder Installation auswählen.
2. Vorhandene Datenquelle auswählen, etwa Home Assistant, Importdatei oder manuelle Eingabe.
3. Bereich, Raum und Installationspunkt bestimmen oder neu anlegen.
4. Asset, Typ, Produkt und technische Eigenschaften anlegen oder auswählen.
5. Zuleitung und vorgelagerten Versorgungspfad auswählen.
6. Schutzgerät, Verteilungsposition, Phase, Leiter, Kabel und Stromkreis erfassen.
7. Nachgelagerte Komponenten auswählen; noch nicht vorhandene Ziele als offenen Entwurf oder Notiz vormerken.
8. Netzwerk- und Verbrauchsinformationen ergänzen, sofern für den Komponententyp relevant.
9. Bilder aus Immich und Dokumente aus Nextcloud auswählen.
10. Notizen, Wiki-Verweise und Wartungspläne ergänzen.
11. Vollständige Vorschau mit Warnungen, offenen Angaben und geplanten Änderungen anzeigen.
12. Zusammenhängend speichern und bei Fehlern möglichst vollständig zurückrollen.

## Verbindliche Leitplanken für den späteren Sprintvertrag

- Der Assistent darf technische Angaben nicht erraten.
- Vorschläge aus Integrationen müssen als Vorschläge sichtbar bleiben.
- Unvollständige Abläufe müssen als Entwurf fortsetzbar sein.
- Bereits vorhandene Objekte sind auswählbar; Duplikate müssen aktiv verhindert werden.
- Vor dem Speichern wird jede Änderung einzeln und als Gesamtplan validiert.
- Teilweise gespeicherte Objektketten sind soweit technisch möglich zu vermeiden.
- Bei unvermeidbaren Teilfehlern muss die Oberfläche eindeutig zeigen, was gespeichert wurde.
- Secrets und interne Integrationsadressen bleiben ausschließlich im Backend.
- Der Assistent nutzt die endgültigen Fach-APIs der Module 0032 bis 0034 und dupliziert keine Geschäftslogik.
- Ein späterer Sprintvertrag muss Backend, Frontend, Migrationen, Entwurfsmodell, Transaktionsgrenzen, Tests und Abnahmekriterien vollständig definieren.

## Noch bewusst offen

- Welche Assistentenvorlagen zum Start angeboten werden.
- Ob Entwürfe lokal, serverseitig oder in beiden Ebenen gespeichert werden.
- Welche Objektketten in einer einzigen Datenbanktransaktion erstellt werden können.
- Wie externe Integrationsoperationen kompensiert werden, wenn lokale Schritte fehlschlagen.
- Welche Netzwerk- und Verbrauchsdaten pro Komponententyp verpflichtend oder optional sind.
- Ob ein generischer Ablauf genügt oder zusätzlich spezialisierte Vorlagen nötig sind, etwa für Wärmepumpe, PV-Anlage, Sicherungskasten, Netzwerkgerät oder Zähler.
