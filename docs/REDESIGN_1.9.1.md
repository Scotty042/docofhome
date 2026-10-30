# DocOfHome 1.9.1 – neue Oberfläche

Die Umsetzung basiert auf dem bereitgestellten Quellpaket 1.9.0 und der ausgewählten Salbei-Variante 1. Es handelt sich um das bestehende Vue-/Vuetify-Frontend mit echten API-Verbindungen. Die separate frühere React-Designvorschau gehört nicht zu diesem Paket.

## Was sich ändert

Helle Flächen, dunkelgrüne Aktionen, große Serifentitel und lokal mitgelieferte Schriftdateien bilden das gemeinsame Design. Navigation, Tabellen, Formulare, Dialoge und Karten verwenden dieselben Grundregeln. Dashboard, Inventarliste und Gerätedetails wurden strukturell überarbeitet. Die übrigen Module erhalten das gemeinsame Erscheinungsbild; ihre Fachabläufe wurden nicht vollständig neu entwickelt.

Alle aktivierten Module bleiben in aufklappbaren Gruppen erreichbar. Unter Einstellungen → Module wählt „Schnellzugriff“ zusätzliche direkte Einträge aus. Die bestehende Einstellung `main_menu_modules` bleibt technisch erhalten. Deaktivierte Module werden ausgeblendet. Die Navigation merkt sich offene Gruppen pro Browsersitzung.

Neue Einrichtungen starten hell. Vorhandene gespeicherte Theme-Einstellungen bleiben wirksam. Für die gezeigte helle Variante bei bisher dunkler Einstellung unter Einstellungen das helle Erscheinungsbild wählen.

Das Dashboard verwendet echte Werte und Fälligkeiten. Abweichungen von Datum, Zahlen und Anzahl der Einträge in der Designvorlage sind datenabhängig. Fehlende Messwerte werden nicht durch Beispieldaten ersetzt. Dashboard-Karten bleiben konfigurierbar; überfällige Aufgaben bleiben sichtbar.

Inventarsuche, Filter, Sortierung und Seite stehen in der URL und bleiben beim Rücksprung aus der Detailansicht erhalten. Gerätedetails gliedern vorhandene Inhalte in vier Registerkarten; Bearbeiten, Archivieren, Ersetzen und Duplizieren bleiben vorhanden.

## Installation erst bei gewünschtem Umstieg

Die laufende Installation wurde nicht verändert. Dieses Paket enthält keine Datenbank, Zugangsdaten oder produktiven Nutzerdaten. Die Browserbelege zeigen ausschließlich lokale Beispieldaten.

Vor einem späteren Umstieg ein vollständiges Backup nach bestehender Projektanleitung erstellen. Das Quellpaket wie bisher als Dockerimage bauen und mit den bestehenden persistenten Daten verwenden. Dockerfile und Compose bleiben unverändert. Gegenüber 1.9.0 ist keine neue Datenbankmigration erforderlich; Alembic-Head bleibt 0061. Der neue Service-Worker-Cache trägt Version 1.9.1.

## Validierung und Grenzen

Details und Screenshots stehen in `../design-qa.md`. Der lokale Backendtest lief unter Python 3.12 statt der im Dockerfile vorgesehenen 3.13. Ein bekannter Backendtestfehler wurde im unveränderten Ausgangspaket reproduziert. Integrationen, tatsächliche Drucker, Cloudkonten und das produktive NAS wurden nicht geprüft. Deshalb enthält das Release-Manifest weiterhin `full_quality_gate_passed: false`.
