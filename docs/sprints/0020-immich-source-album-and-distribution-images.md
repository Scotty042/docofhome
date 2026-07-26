# Sprint 0020 – Immich-Quellalbum und Verteilungsbilder

## Status

Lokal implementiert; Docker-Validierung steht mangels lokaler Docker-/Podman-Laufzeit aus.

## Ziel

Immich bleibt bewusst klein: In den Einstellungen wird genau ein Quellalbum gewählt. Bei Assets
und elektrischen Verteilungen lassen sich anschließend Bilder aus allen Seiten dieses Albums
suchen und manuell verknüpfen.

## Umfang

- persistente, optionale Immich-Album-ID in den Integrationseinstellungen
- Albumliste und Auswahl direkt in den Einstellungen
- Asset-Bildauswahl ausschließlich aus dem gewählten Album
- 48 Vorschaubilder pro Seite, Dateinamensuche, sichtbare Treffer- und Seitenangaben sowie Zugriff
  auf sämtliche Ergebnisseiten
- Fotoverwaltung auf Verteilungsdetails über die bereits vorhandene Asset-Identität der Verteilung
- sichtbare Mouse-over-Hinweise für reine Icon-Aktionen in Verteilungsansichten
- additive Migration `0014` ohne Änderung bestehender Verknüpfungen

## Nicht im Umfang

- Uploads oder Änderungen in Immich
- mehrere gleichzeitig ausgewählte Quellalben
- automatische Fotozuordnung
- eigene Fototabellen für Verteilungen
- weitere Immich-Filter oder neue Fotoziele für Räume und Stromkreise

## Abnahme

- ein Album lässt sich in den Einstellungen laden, auswählen und dauerhaft speichern
- Asset- und Verteilungsdialoge senden die gespeicherte Album-ID bei jeder Bildsuche
- sämtliche Albumseiten bleiben über Pagination erreichbar
- Verteilungsbilder sind auch auf dem zugrunde liegenden Asset sichtbar und umgekehrt
- unklare Icon-Aktionen zeigen beim Mouse-over ihre Bedeutung
- Backend-, Frontend-, Typ-, Build- und Migrationsprüfungen sind erfolgreich
