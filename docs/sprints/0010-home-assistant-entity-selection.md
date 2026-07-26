# Sprint 0010: Manuelle Home-Assistant-Entitätsauswahl

- Status: Approved
- Target branch: `feature/home-assistant-entity-selection`
- Depends on: PR #10, migration `0010`, ADR-0006 und ADR-0008

> Dieses Dokument ist der vollständige Implementierungsvertrag für diesen Sprint. Zusätzlich gelten
> die verbindlichen Regeln aus `docs/DEVELOPMENT_GUIDELINES.md`.

## Ziel

Benutzer können festlegen, ob Tectoryn alle aus Home Assistant gelesenen Entitäten oder nur eine
explizit ausgewählte Teilmenge in der normalen Smart-Home-Ansicht zeigt. Die Auswahl wird dauerhaft
und update-sicher in Tectoryn gespeichert, funktioniert mit mehreren Tausend Entitäten und verändert
weder Home Assistant noch bestehende Asset-Zuordnungen.

## Hintergrund

Die read-only Home-Assistant-Integration liest Konfiguration, Zustände sowie Geräte-, Entitäts- und
Bereichsregister und stellt diese in der Smart-Home-Seite dar. Große Installationen können mehrere
Tausend Entitäten enthalten. Eine lokale manuelle Auswahl reduziert die sichtbare Arbeitsmenge und
erleichtert die Dokumentation, ohne Schaltbefehle oder Schreibzugriffe an Home Assistant einzuführen.

Die Home-Assistant-REST- und WebSocket-Schnittstellen liefern weiterhin vollständige Snapshots. Die
Auswahl ist deshalb bewusst ein lokaler Sichtbarkeitsvertrag und keine Zusage, dass Home Assistant
weniger Daten überträgt. Diese Entscheidung ist in ADR-0008 dokumentiert.

## Anforderungen

- Es existieren die Modi `all` und `selected`.
- `all` ist der update-kompatible Standard und zeigt alle gelesenen Entitäten.
- `selected` zeigt ausschließlich explizit gespeicherte Entitäts-IDs.
- `selected` mit leerer Auswahl ist gültig und zeigt keine Entitäten oder daraus abgeleiteten Geräte.
- Entitäts-IDs werden getrimmt, eindeutig gespeichert, stabil sortiert gelesen und auf höchstens
  255 Zeichen sowie das Format `domain.object_id` begrenzt.
- Ein vollständiges Ersetzen von Modus und Auswahl erfolgt atomar in einer Transaktion.
- Die Auswahl bleibt erhalten, wenn Home Assistant nicht erreichbar ist oder eine ausgewählte
  Entität vorübergehend nicht im Snapshot vorkommt.
- Unbekannte gespeicherte Entitäts-IDs werden nicht automatisch gelöscht.
- Bestehende Home-Assistant-Asset-Zuordnungen bleiben beim Auswählen und Abwählen unverändert.
- Tectoryn sendet weiterhin keine Schalt-, Konfigurations- oder Registrierungsbefehle an Home
  Assistant.
- Integration-Ausfälle blockieren keine lokale Tectoryn-Funktion außerhalb des Smart-Home-Moduls.
- Die Auswahloberfläche funktioniert in Dark und Light Mode sowie auf Desktop und Mobilgeräten.

## Backend

### Datenmodell

- `home_assistant_selection_settings` enthält höchstens die Singleton-Zeile `id = 1` mit dem Modus
  `all` oder `selected`, `created_at` und `updated_at`.
- Fehlt die Singleton-Zeile, gilt aus Update-Kompatibilitätsgründen der Modus `all`.
- `home_assistant_entity_selections` enthält eine stabile UUID, eine eindeutige `entity_id` sowie
  `created_at`.
- Datenbank-Constraints sichern Singleton-ID, erlaubte Modi, nicht leere Entitäts-IDs und
  Eindeutigkeit ab.
- Es werden keine Benutzerwerte, Asset-Zuordnungen oder externen Daten kopiert oder überschrieben.

### API

- `GET /api/v1/home-assistant/selection` liefert Modus, sortierte Entitäts-IDs und Anzahl.
- `PUT /api/v1/home-assistant/selection` ersetzt Modus und vollständige Auswahl atomar.
- Der Payload enthält `mode` und `entity_ids`; doppelte IDs werden normalisiert.
- Mehr als 10.000 übermittelte IDs werden mit HTTP 422 abgelehnt.
- `GET /api/v1/home-assistant/entities` erhält additiv `selection_scope=visible|all`.
- `visible` ist Standard und wendet den gespeicherten Modus an.
- `all` umgeht ausschließlich den lokalen Sichtbarkeitsfilter und dient der Auswahloberfläche.
- `GET /api/v1/home-assistant/devices` erhält denselben additiven Parameter.
- Im Modus `selected` sind nur Geräte sichtbar, die mindestens eine aktuell sichtbare ausgewählte
  Entität besitzen. Ihre `entity_count` zählt nur diese sichtbaren Entitäten.
- Bestehende Such-, Bereichs-, Domain-, Geräte-, Verfügbarkeits- und Pagingfilter werden nach der
  Sichtbarkeitsauswahl angewendet.
- Die Summary behält die bisherigen Gesamtzahlen und ergänzt Modus, ausgewählte Anzahl sowie
  sichtbare Geräte- und Entitätszahlen.

### Schichten

- Router übersetzen ausschließlich HTTP und bekannte Domänenfehler.
- `HomeAssistantSelectionRepository` besitzt Lesen und atomisches Ersetzen der lokalen Auswahl.
- `HomeAssistantSelectionService` besitzt Normalisierung, Formatprüfung und Transaktionsgrenze.
- `HomeAssistantService` liest die Auswahl über das Repository und wendet sie auf den gecachten
  vollständigen Snapshot an.
- Externe Netzwerkzugriffe bleiben ausschließlich im bestehenden Home-Assistant-Service.

## Frontend

- Die Smart-Home-Seite zeigt den aktiven Modus und die sichtbaren Zahlen verständlich an.
- Eine Schaltfläche `Entitäten auswählen` öffnet einen Dialog für die lokale Auswahl.
- Der Dialog lädt die Auswahl unabhängig vom externen Snapshot und alle verfügbaren Entitäten mit
  `selection_scope=all` paginiert ohne stille 100- oder 1.000-Einträge-Grenze.
- Der Dialog bietet Suche, Domainfilter, `Alle anzeigen` und `Nur ausgewählte Entitäten`.
- Auswahländerungen bleiben beim Suchen und Filtern im Dialog erhalten.
- Benutzer können zwischen `Alle Entitäten anzeigen` und `Nur ausgewählte Entitäten anzeigen`
  wechseln.
- Im Modus `selected` kann eine leere Auswahl bewusst gespeichert werden.
- Speichern sendet den vollständigen, deduplizierten Satz und lädt Übersicht, Geräte und Entitäten
  anschließend neu.
- Abbrechen verwirft ungespeicherte Änderungen.
- Lade-, Leer-, Fehler- und Erfolgszustände sind verständlich.
- Auf Mobilgeräten bleiben Auswahlzeilen und Aktionen bedienbar; lange technische IDs dürfen
  umbrechen.
- Bestehende Asset-Zuordnungsfunktionen bleiben unverändert erreichbar.

## Migrationen

- Migration `0011` folgt auf `0010`.
- Sie erstellt ausschließlich `home_assistant_selection_settings` und
  `home_assistant_entity_selections` samt Constraints und Index.
- Es wird keine Singleton-Zeile vorbefüllt; fehlende Konfiguration bedeutet `all`.
- Upgrade von `0010`, frisches Upgrade auf `head`, Downgrade auf `0010`, Alembic-Check und
  `PRAGMA foreign_key_check` müssen erfolgreich sein.
- Bestehende UUIDs, Settings, Assets, Links, Integrationsgeheimnisse und Persistenzdaten bleiben
  unverändert.

## Tests

- Backend-Service- und API-Tests für Standardmodus, leere Auswahl, Deduplizierung, Sortierung,
  ungültige IDs, atomisches Ersetzen und Persistenz nach neuer Session.
- Filtertests für sichtbare/all Entitäten, abgeleitete Geräte, Zählwerte, Suche und Paging.
- Regressionstest mit mehr als 1.000 verfügbaren Entitäten ohne Datenverlust.
- Test, dass Abwählen bestehende Asset-Zuordnungen nicht löscht.
- Direkte Datenbanktests für Singleton-, Mode-, Not-empty- und Unique-Constraints.
- Migrationstest von `0010` mit vorhandener Home-Assistant-Asset-Zuordnung sowie Downgrade.
- Frontend-Transporttests für GET/PUT und `selection_scope`.
- Frontend-Helfertests für Deduplizierung, stabile Sortierung, Filterung, mehr als 1.000 Entitäten und
  Erhalt der Auswahl über Suchfilter hinweg.
- Ruff, mypy, pytest, Alembic-Upgrade/-Check, Vitest, `vue-tsc`, Vite-Build und Docker-Build.

## Definition of Done

- [ ] Jeder Vertrag dieses Sprints ist implementiert.
- [ ] Keine Funktion außerhalb des Sprintumfangs wurde eingeführt.
- [ ] Backend- und Frontend-Verträge sind typisiert und dokumentiert.
- [ ] Migration `0011` ist additiv und update-sicher.
- [ ] Auswahl, Leerzustand, Fehlerpfade, Paging und Persistenz sind getestet.
- [ ] Bestehende Asset-Zuordnungen und Home-Assistant-Read-only-Grenzen bleiben erhalten.
- [ ] Ruff, mypy, pytest, Alembic, Vitest, vue-tsc, Vite und Docker sind grün.
- [ ] README, CHANGELOG, ADR, Architekturübersicht und Sprintstatus sind aktuell.
- [ ] Der Pull Request enthält keine Zugangsdaten, privaten URLs oder generierten Benutzerdaten.
- [ ] Die Abnahmekriterien sind nachweisbar erfüllt.

## Abnahmekriterien

1. Eine aktualisierte Installation startet ohne neue Auswahlkonfiguration weiterhin im Modus `all`.
2. Benutzer können eine beliebige Teilmenge aus mehr als 1.000 Entitäten dauerhaft auswählen.
3. `selected` mit leerem Satz zeigt bewusst null Entitäten und null abgeleitete Geräte.
4. Normale Smart-Home-Listen wenden die Auswahl an; der Auswahldialog kann weiterhin alle externen
   Entitäten laden.
5. Abgewählte oder vorübergehend fehlende Entitäten verlieren weder ihre gespeicherte Auswahl noch
   vorhandene Asset-Zuordnungen automatisch.
6. Home Assistant empfängt keine Schreib- oder Schaltbefehle.

## Nicht Bestandteil

- Schreiben, Schalten oder Konfigurieren von Home Assistant.
- Serverseitige Home-Assistant-Filterabonnements oder inkrementelle Registry-Synchronisation.
- Automatische Auswahl anhand von Bereichen, Domains, Labels oder Integrationen.
- Auswahl kompletter Geräte als eigenständiger persistenter Vertrag.
- Löschen von Asset-Zuordnungen beim Abwählen.
- Immich-, Nextcloud-, Wiki-, Wartungs- oder Verbrauchsfunktionen.
