# AMS-Lagerrollen und originale Bambu-Bilder

## AMS-Belegung

Zugeordnete Plätze zeigen dieselbe physische Rolle wie der Lagerbestand: Hersteller, Variante, Farbname/Farbcode, Rollen-ID und vorhandenes Bild. „Lagerrolle öffnen“ öffnet ihre Details. Lagerrestmenge und AMS-Prozentmeldung sind getrennt beschriftet und bleiben Schätzungen bzw. Beobachtungen. Nullwerte werden angezeigt. Ein alter Snapshot wird weiterhin gekennzeichnet.

Die technische AMS-/Slotnummerierung bleibt erhalten. Drucker werden getrennt gruppiert. Leere oder nicht eindeutig zugeordnete Plätze werden nicht aufgrund ähnlicher Farbe einer Rolle zugeschlagen. Mit „Rolle zuordnen“ lässt sich die Lagerrolle nach Name, Farbe oder ID suchen. Die vorhandene Identitäts-/Wechsellogik bleibt unverändert.

## Store-Bilder ergänzen

Nach dem Update unter Filament-Sammlung → Rollenbestand den Knopf „Store-Bilder ergänzen“ verwenden. Ein Durchlauf bearbeitet die aktiven Bambu-Rollen ohne Bild, unabhängig von den gerade gesetzten Ansichtsfiltern. Bestehende eigene Bilder bleiben bestehen. Fortschritt und nicht zuordenbare Rollen werden angezeigt. Andere Hersteller und archivierte Rollen werden ausgelassen.

1. Ist eine fünfstellige Shop-Farbnummer vorhanden, wird sie verwendet.
2. Andernfalls wird der gespeicherte Cloud-Produktcode, etwa A00-P6, exakt mit der Hersteller-SKU im öffentlichen offiziellen japanischen Bambu-Shop-Katalog verglichen. Der Katalog enthält im Unterschied zur aktuellen EU-Seite diese ursprünglichen SKUs.
3. Die Farbnummer wird innerhalb derselben Materialvariante im deutschen EU-Katalog geprüft. Nur ein eindeutig übereinstimmendes Bild wird übernommen und lokal gespeichert.
4. Fehlende Shopnummern und Farbnamen werden ergänzt. Eigene Namen und vorhandene Bilder werden nicht automatisch überschrieben.

Kein Abgleich über annähernde Farben. Unbekannte, alte oder widersprüchliche Produktcodes sowie nicht verfügbare Produktseiten bleiben zur Prüfung offen. Dann genügt oft das Ergänzen der Shop-Farbnummer; bei nicht unterstützter Variante bleibt die manuelle Bildwahl möglich. Ein einzelnes Problem stoppt den restlichen Durchlauf nicht.

Beispiel nach öffentlicher Live-Prüfung vom 30.10.2026: A00-P6 → PLA Basic, Magenta (10202). PLA Basic, Hellgrau (10104), verwendet das vom Nutzer gezeigte Modellbild. Quellen: https://bambu-lab-jp.myshopify.com/products/pla-basic-filament.js und https://eu.store.bambulab.com/de/products/pla-basic-filament . Diese öffentlichen Store-Formate können sich ändern.

Der Bildabgleich wird ausdrücklich gestartet, nicht beim bloßen Öffnen der Sammlung. Er verwendet keine Bambu-Konto-Zugangsdaten. Produktbilder werden lokal gespeichert; ein Katalogabruf wird während eines Durchlaufs bis zu einer Stunde wiederverwendet. Es werden weder AMS-Zuordnungen noch Cloud-Rollen durch den Bildabgleich geändert.

## Umstieg

Wie bisher aus dem Quellpaket bauen bzw. GitHub-Release `v1.9.3` verwenden. Bestehende Datenordner, Netzwerke und Einstellungen beibehalten; keine neue Datenbankmigration gegenüber 1.9.2. Vor dem späteren Umstieg vollständig sichern. Die laufende NAS-Installation wurde während der Entwicklung ausschließlich gelesen.
