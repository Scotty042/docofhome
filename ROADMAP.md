# DocOfHome – Roadmap

Stand: 27. Juli 2026

## Abgeschlossen bis 1.0.0

- Kernmodule für Assets, Orte, Elektro, Netzwerk, Verbrauch, Wartung und Wissen;
- optionale read-only Integrationen und sichere Dokument-/Backupabläufe;
- mobile Zählererfassung und responsive Monats-/Jahresstatistik;
- persistentes Dashboard und kalenderbasierte Termine/Erinnerungen;
- Switch-Portgenerator, dokumentierter Netzwerkpfad und FRITZ!Box-Zuordnung;
- logische Workloads unter Host-Assets;
- JSON-/CSV-Portabilität und fachlich lesbare Änderungshistorie;
- geführter modulübergreifender Fachassistent.

## Abgeschlossen mit 1.1.x

- eigene Statistikskalierung je Zähler;
- robuste Dashboard-Zuordnung für Strom und Gas;
- Ableseerinnerungen unter **Wartung & Aufgaben**;
- visuelle Immich-Auswahl bei Zählerständen;
- PV- und Energiebilanz einschließlich Netzanschluss, PV-Quellen,
  Wechselrichtern und Speichern;
- mehrere Energiequellen in der Elektro-Topologie;
- Asset-/Ortszuordnung und HA-Livewerte bei Zählern;
- N-/PE-Schienen, Zählerplatzierung und hierarchische Ortsauswahl;
- logische Netzwerkinterfaces und gerätebezogene Verkabelungsprüfung;
- Migrationen `0027` und `0028`.

## Abgeschlossen mit 1.2.0

- HA-Performanceprofil für mehrere Tausend Entitäten;
- serverseitige Pagination, Filter, gebündelte Synchronisierung und Caches;
- HA-Mehrfachzuordnungen und Entitätsrollen je Asset;
- allgemeine DIN-Hutschienengeräte und Livewerte im Zählerschrank;
- links/rechts geteilte Schrankebenen für N und PE;
- vier Produktbildquellen mit kontrollierbarer Online-Suche;
- Asset-Duplikate, Serienanlage und optionale fortlaufende TE-Platzierung;
- Inline-Labels und einklappbare Navigation **Mehr**;
- Migration `0029`.

## Bereinigt mit 1.2.1

- aktueller Projektstatus und Backlog als eindeutige Freigabequelle;
- zentrales Sprintregister;
- historische, widersprüchliche Übergabe in das Archiv verschoben;
- Sprint 0039 als nicht freigegebener Entwurf dokumentiert;
- Release-, Update- und Qualitätsstatus auf 1.2.1 vereinheitlicht.

## Korrigiert mit 1.2.2

- Frontend-Buildfehler durch das nicht verfügbare Icon
  `mdi-label-plus-outline` behoben;
- Inline-Labelanlage verwendet nun das in `@mdi/font` 7.4.47 verfügbare
  `mdi-tag-plus-outline`;
- keine Datenmodell- oder Migrationsänderung; Alembic-Head bleibt `0029`.

## Korrigiert mit 1.2.3

- Test-Fixture der Immich-Galerie um die Einstellung
  `online_product_image_search_enabled` ergänzt;
- Typvertrag der Album-Hilfsfunktion auf `integrations` begrenzt, damit
  fachfremde neue Konfigurationspflichtfelder keine erneuten Buildfehler
  auslösen;
- keine Datenmodell- oder Migrationsänderung; Alembic-Head bleibt `0029`.

## Korrigiert mit 1.2.4

- Wikimedia-Produktbildsuche mit serverseitigem Primärweg und direktem
  Browser-Fallback;
- lokale Speicherung ausgewählter Online-Bilder und differenzierte
  Fehlerzustände;
- Netzwerkseite ohne den bisherigen HTTP-500-Fehler, mit robusten Altwerten und
  fehlertoleranten Teilabfragen;
- Schrankaufteilung für Haupt- und Unterverteilungen einschließlich einfacher
  Reihenansicht und strukturiertem Feld-/Bereichsmodus;
- globale Benachrichtigungen oberhalb von Dialogen und sichere mobile
  Zählerstandserfassung;
- Migration `0030` zur Freigabe strukturierter Unterverteilungen.

## Erweitert mit 1.3.0

- passive Phasenverteilerblöcke, Sammelschienen, N-/PE-Schienen und Klemmen als
  Nicht-Asset-Objekte im Zählerschrank;
- L1/L2/L3/N/PE-Zuordnung und technische Angaben je Schrankkomponente;
- Verkabelung und Versorgungstopologie über den Endpunkttyp
  `cabinet_component`;
- gemeinsame TE-Kollisionsprüfung für Schutzgeräte, DIN-Assets und
  Schrankkomponenten;
- Drag-and-drop für Schutzgeräte in einfachen Reihenaufteilungen von Haupt- und
  Unterverteilungen;
- korrigierte Serienplatzierung im Reihenmodus;
- Migration `0031`.

## Korrigiert und erweitert mit 1.3.1

- normale DIN-Assets im gemeinsamen TE-Raster statt in einer separaten Liste;
- Drag-and-drop für Schutzgeräte und DIN-Assets in Reihen- und Bereichslayouts;
- optionale DIN-Breite direkt am Asset und als Standard am Asset-Typ;
- Produktstammsatz für die DIN-Platzierung nicht mehr zwingend;
- mehrere Einspeisungen an passiven Schrankkomponenten;
- Prüfung, dass nur konfigurierte und tatsächlich eingespeiste Leiter
  weitergeführt werden;
- laufender Verbrauchsmonat wird bis heute statt bis zum Folgemonat bewertet;
- Migration `0032`.

## Abgeschlossen mit 1.4.1

### Sprint 0039: Über DocOfHome, Changelog, Impressum und Feedback

Umgesetzter Umfang:

- zentrale Seite **Mehr → Über DocOfHome**;
- kurze Projektbeschreibung mit Zweck und Motivation;
- aktuelle Version, Release-Historie und Changelog;
- konfigurierbarer GitHub-/Repository-Hinweis;
- pflegbares Impressum;
- optionales Feedbackformular;
- ausschließlich serverseitiger Upload als Text- oder Markdown-Datei in einen
  freigegebenen Nextcloud-WebDAV-Zielordner.

Der Sprint wurde mit Release 1.4.1 umgesetzt. Der damalige konfigurierbare
Impressums- und Feedbackansatz wurde mit 1.4.2 durch feste Projektangaben und
einen direkten ZIP-Upload ersetzt. Der vollständige ursprüngliche Entwurf liegt unter
[`docs/sprints/0039-about-changelog-imprint-feedback.md`](docs/sprints/0039-about-changelog-imprint-feedback.md).

## Weitere Zukunftskandidaten

Noch nicht nummeriert und nicht priorisiert:

- optionale Authentifizierung und Mehrbenutzerrollen;
- optionale, ausdrücklich aktivierte read-only Workload-Erkennung;
- getrennte Messung von Speicher-Lade-/Entladeflüssen und Leistungskurven;
- erweiterte Druck- und Berichtsvorlagen;
- zusätzliche versionierte Importadapter für Fremdformate.
- UGREEN-UGOS-Docker-API-Anbindung als read-only Integrationskandidat; die
  bereits verifizierten Endpunkte, Datenfelder, Sicherheitsanforderungen und
  offenen Berechtigungsfragen sind unter
  [`docs/backlog/ugreen-ugos-docker-api.md`](docs/backlog/ugreen-ugos-docker-api.md)
  dokumentiert. Die Umsetzung ist bewusst zurückgestellt.

## Umgesetzt mit 1.7.15 – Lebenslaufakten und Paperless-Verknüpfung

- strukturierte Profile für Bezugsobjekte, insbesondere Fahrzeuge, Tiere, Anlagen und Geräte;
- Tätigkeitstypen für Wartung, Inspektion, Reparatur, Messung, Impfung, Termin, TÜV/Prüfung, Schornsteinfeger und Service;
- gemeinsamer Zeitstrahl je Bezugsobjekt mit vergangenen Durchführungen und offenen zukünftigen Fälligkeiten;
- Paperless-ngx als optionale, serverseitige Read-only-Integration mit URL und API-Token;
- manuelle Suche und Verknüpfung bestehender Paperless-Dokumente an Historieneinträge;
- ausschließlich Referenz/Metadaten in DocOfHome, keine PDF-Kopie und keine automatische Dokumentzuordnung;
- Migration `0055`.

## Planungsregel

Ein Zukunftspunkt wird erst dann implementiert, wenn ein konkreter Sprintvertrag
als **Approved** markiert wurde. Bis dahin gilt er ausschließlich als Backlog oder
Entwurf. Ausstehende Build- und Zielsystemprüfungen für 1.2.x sind Qualitätsgates,
keine Funktionssprints.

## Korrigiert mit 1.3.2

- Reparaturmigration `0033` für bestehende Datenbanken mit dem veralteten
  Ein-Ziel-eine-Quelle-Index;
- Mehrfacheinspeisungen an Verteilerblöcken funktionieren auch nach Updates aus
  bereits migrierten Altständen;
- verständliche deutsche Meldungen für Topologie-Datenbankkonflikte.



## Umgesetzt mit 1.4.0 – private Elektro-Gruppen und Schrankansicht

- Sammelschienen mit TE-Spanne, Startphase und wiederholter L1/L2/L3-Folge;
- FI-Gruppen und je FI zugeordnete N-Schienen;
- automatische Phase-, FI- und N-Schienen-Ermittlung für Schutzgeräte;
- Warnungen statt harter Blockaden bei unvollständiger Hausdokumentation;
- Belegungsübersicht, Kompakt-/Erweitert-Modus, Detailpanel und sichtbare
  Sammelschienen im gemeinsamen TE-Raster.

Bewusst nicht Teil dieses Sprints sind nummerierte Einzelklemmen, Aderlisten,
Kurzschluss-/Selektivitätsberechnungen und eine normgerechte Elektro-CAD-Ausgabe.


## Vereinfacht mit 1.4.2 – Veröffentlichung und Feedback

- konfigurierbares Impressum vollständig entfernt;
- Projekt- und spätere GitHub-Verweise zentral im Quellcode;
- direkt aktives Feedback als begrenztes ZIP;
- serverseitiger Upload an einen festen öffentlichen Nextcloud File Drop;
- keine Abhängigkeit von der privaten Nextcloud-Integration des Anwenders.


## Umgesetzt mit 1.5.0 – Handbuch & Glossar

- statische, offline nutzbare Hilfeseite unter **Wiki**;
- zentrale Inhalte für Einstieg, Assets, Elektro, Netzwerk, Verbrauch, Home
  Assistant, Medien und Betrieb;
- Suche, Kategorienfilter, A–Z-Glossar, Sprungmarken und responsive Bedienung;
- interne Anker wie `/wiki/handbuch#begriff-sammelschiene`;
- Asset-Bearbeitung direkt aus der Detailansicht platzierter DIN-Geräte;
- keine Datenbankmigration und keine Veränderung vorhandener Wiki-Seiten.

Bewusst offen bleiben kontextsensitive Hilfe-Icons in weiteren Dialogen sowie
eine spätere redaktionelle Erweiterung der statischen Inhalte.


## Umgesetzt mit 1.6.0 – Elektroansicht, Stammdaten und Messpunkte

- Assistentenstatus und Abschlussnavigation korrigiert;
- DocOfHome-Backupnamen mit Legacy-Kompatibilität;
- verbesserte Online-Bildsuche;
- Desktop-/Tablet-orientierte, farbcodierte DIN-Schrankansicht;
- elektrische Zählerfilterung;
- Sicherungsautomat-Stammdaten und Stromstoßschalter;
- CT-/Stromwandler-Messpunkte an bestehenden Verkabelungen;
- Home-Assistant-Zuordnung je Smart-Meter-Messkanal;
- erweiterte Elektrobegriffe im Handbuch.

## Konsolidiert mit 1.6.3 – Elektro-Integrität

- gemeinsame Phasenberechnung für Phasenschienen, Schutzgeräte, Stromkreise,
  Topologie und Messpunkte;
- automatisch verwaltete physische Kammschienen-Verbindungen;
- klare Abgrenzung zur allgemeinen manuellen Sammelschiene;
- konsistente FI-/N-/PE-Gruppen und Lebenszyklusprüfungen;
- Smart-Meter-Messphasen gegen wirksame Leiter validiert;
- Migration `0043` zur Bestandsreparatur und Datenbankabsicherung.
