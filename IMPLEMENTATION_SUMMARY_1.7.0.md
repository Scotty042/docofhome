# DocOfHome 1.7.0 – Umsetzungsübersicht

Die Version setzt den freigegebenen Umfang des Runbooks 1.7 in der bestehenden FastAPI-/SQLModel- und Vue-/Vuetify-Anwendung um.

| Paket | Umsetzung |
| --- | --- |
| DOH-1701 | Globale Meldungen werden per Teleport oberhalb von Modalen gestapelt; feldbezogene Validierung bleibt erhalten. |
| DOH-1702 | Schnittstellengeschwindigkeit ist auf 100, 1000 und 2500 Mbit/s begrenzt und wird einheitlich formatiert. |
| DOH-1703 | Dokumentierte und erkannte IPs werden getrennt gespeichert, per normalisierter MAC abgeglichen und mit Status, Konflikten, Übernahme, Ignorieren und Audit dargestellt. |
| DOH-1704 | FRITZ!Box-Geräte werden numerisch nach IPv4-Adresse sortiert; ungültige Adressen stehen am Ende. |
| DOH-1705 | Hostname-Fehler nennen unzulässige Unterstriche konkret und schlagen Bindestriche vor. |
| DOH-1706 | Switch-Fronten bleiben zweireihig, horizontal scrollbar und unterstützen konfigurierbare physische Portmuster. |
| DOH-1707 | Zähler werden über die stabile Capability `is_meter` erkannt; bestehende Zählertypen werden migriert. |
| DOH-1708 | Monatsend-Ablesungen erscheinen im konfigurierten Vorlauf oder standardmäßig drei Tage vorher und bleiben periodengenau/idempotent. |
| DOH-1709 | Gerätekarten wurden verdichtet und für Desktop, Tablet und Mobil neu gerastert. |
| DOH-1710 | Einzelne Assets und Asset-Typen erhalten eigene JPEG-/PNG-/WebP-Bilder mit Optimierung, Entfernen und Fallback. |
| DOH-1711 | Neue/geänderte Stromkreise benötigen ein aktives, platziertes, geeignetes und nicht anderweitig belegtes Endschutzgerät derselben Verteilung. |
| DOH-1712 | Die Phasenherkunft wird als Kammschiene, Draht oder manuell geführt; reale Verbindungen haben Vorrang und veraltete Schienensperren werden repariert. |

## Release-Technik

- Zielversion: `1.7.0`
- Alembic-Head: `0046`
- Migration mit Upgrade-/Downgrade-Prüfung
- Regressionstests für die neuen Kernregeln ergänzt
- Statische Python-, Vue-/TypeScript-, JSON- und TOML-Prüfungen erfolgreich

Die noch vorgeschriebenen produktionsnahen Smoke-Tests und der vollständige CI-Lauf sind in einer Umgebung mit allen Entwicklungsabhängigkeiten durchzuführen. Details stehen in `VALIDATION_1.7.0.md`.
