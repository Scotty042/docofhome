# DocOfHome 1.7.0

Version 1.7.0 konzentriert sich auf Datenintegrität in der Elektro-Dokumentation, einen nachvollziehbaren IP-Abgleich und kompaktere Bedienoberflächen.

## Wichtige Änderungen

- Jeder neue oder geänderte Stromkreis benötigt eine konkrete Sicherung, einen Leitungsschutzschalter oder einen RCBO aus derselben Verteilung. Bereits belegte einpolige Endschutzgeräte können nicht doppelt verwendet werden.
- Die Phase stammt vorrangig aus einer aktiven Kammschiene, danach aus einer aktiven Draht-/Kabelverbindung. Nur ohne physische Einspeisung bleibt eine manuelle Auswahl möglich.
- Zähler werden über eine stabile Capability erkannt. Bestehende Zählertypen werden bei der Migration automatisch gekennzeichnet.
- Monatliche Ableseaufgaben erscheinen im eingestellten Vorlauf, standardmäßig drei Tage vor Monatsende.
- Unter **Netzwerk > IP-Adressen** werden dokumentierte und durch die FRITZ!Box beobachtete Adressen getrennt angezeigt und über die MAC-Adresse abgeglichen.
- Switch-Fronten bleiben zweireihig; am Asset-Typ kann zwischen ungerade/gerade und einer Aufteilung in zwei fortlaufende Port-Hälften gewählt werden.
- Individuelle Bilder können direkt am Asset oder am Asset-Typ gespeichert werden. Uploads werden in WebP umgewandelt und verkleinert.

## Migration und Nacharbeit

Alembic-Migration `0046` ergänzt die neuen Felder und Tabellen. Bestehende Stromkreise ohne Schutzgerätezuordnung werden nicht blockiert, sondern in der Detailausgabe als fehlende Zuordnung kenntlich gemacht. Nach dem Update sollten diese Datensätze sowie gemeldete IP- und Phasenabweichungen geprüft werden.

Vor dem Update sind Datenbank und Medienordner zu sichern. Ein Schema-Downgrade ohne Wiederherstellung des passenden Backups ist nicht vorgesehen.
