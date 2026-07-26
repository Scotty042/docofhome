# DocOfHome 1.2.4

DocOfHome 1.2.4 ist ein Patch-Release für vier gemeldete Fehler in der
Produktbildsuche, der elektrischen Schrankaufteilung, dem Netzwerkmodul und der
Benachrichtigungsdarstellung.

## Online-Produktbilder

Die serverseitige Wikimedia-Suche bleibt der bevorzugte Weg. Kann der
DocOfHome-Container Wikimedia wegen DNS, TLS, Proxy, Firewall oder eines
externen Ausfalls nicht erreichen, versucht das Frontend die offizielle
Wikimedia-API direkt aus dem Browser mit CORS-Unterstützung.

- nur `commons.wikimedia.org` und `upload.wikimedia.org` werden akzeptiert;
- frühere Suchläufe werden bei einem neuen Suchbegriff abgebrochen;
- Suche, Download und Upload besitzen Zeitlimits;
- erst der ausdrücklich ausgewählte Treffer wird übernommen;
- der Browser lädt den Treffer bei Bedarf herunter und überträgt ihn über den
  bestehenden Upload-Endpunkt zur lokalen Speicherung in DocOfHome;
- Fehlermeldungen unterscheiden Backend-Ausfall, externe Nichterreichbarkeit,
  leere Trefferlisten und fehlgeschlagene Bilddownloads.

Upload, Immich-Auswahl und manuelle URL bleiben erhalten.

## Schrankaufteilung von Unterverteilungen

Die Schrankaufteilung ist nun bei Haupt- und Unterverteilungen aufrufbar.
Einfache Reihen werden direkt auf der Schrankseite angezeigt. Bei noch nicht
konfigurierten Verteilungen erscheint ein klarer leerer Zustand mit Aktion zum
Anlegen der Aufteilung.

Unterverteilungen dürfen zusätzlich den strukturierten Feld-/Bereichsmodus
verwenden. Damit können auch dort Felder, Gerätebereiche, Zählerfelder,
N-/PE-Schienen, DIN-Geräte und Schutzgeräte dokumentiert werden.

Dafür wird die additive Migration `0030_enable_subdistribution_sections`
ausgeführt. Sie entfernt ausschließlich die frühere Einschränkung, nach der
Unterverteilungen zwingend den Reihenmodus verwenden mussten.

## Netzwerkmodul

Der HTTP-500-Fehler der Netzwerkseite wurde behoben. Ursache war eine fehlende
Enum-Einbindung bei der Erstellung der Netzwerkübersicht. Zusätzlich werden
unbekannte oder ältere Enum-Werte kontrolliert auf neutrale Standardwerte
abgebildet.

Die Netzwerkseite lädt ihre Teilbereiche nun fehlertolerant: Scheitert ein
Einzelendpunkt, bleiben erfolgreich geladene Geräte, IP-Netze, Schnittstellen,
Verbindungen oder Topologiedaten sichtbar. Freie Switch-Ports bleiben ein
neutraler Zustand; die Verkabelungsprüfung bleibt gerätebezogen.

## Globale Benachrichtigungen

Eine globale Warteschlange zeigt Erfolg-, Warn- und Fehlermeldungen oberhalb von
Dialogen und Vollbilddialogen an. Fehlermeldungen bleiben länger sichtbar,
können manuell geschlossen werden und werden nacheinander dargestellt.

Bei der mobilen Zählerstandserfassung bleibt der Dialog bei einem Speicherfehler
mit allen Eingaben geöffnet. Während des Requests ist die Speichern-Schaltfläche
gesperrt; nach erfolgreichem Speichern schließt der Dialog und die Bestätigung
ist sichtbar.

## Kompatibilität

- Ausgangsbasis: DocOfHome 1.2.3;
- neuer Alembic-Head: `0030`;
- bestehende Assets, Verteilungen, Netzwerkdaten, Zähler, HA-Zuordnungen und
  Produktbilder bleiben erhalten;
- keine Änderung an der Docker-/Compose-Architektur;
- der bestehende Einzelcontainer und `compose.yaml` bleiben gültig.

## Build-Korrektur

Die neu hinzugefügten Frontend-Regressionsprüfungen verwenden Vite-`?raw`-
Imports zum Einlesen der geprüften Vue-Quelldateien. Damit werden die Tests
weiterhin von `vue-tsc` erfasst, ohne `node:fs` oder zusätzliche
`@types/node`-Deklarationen zu benötigen. Der Docker-Schritt `npm run build`
bricht dadurch nicht mehr mit `TS2307` an den fünf neuen Testdateien ab.

