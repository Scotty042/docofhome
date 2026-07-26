# Bekannte Grenzen DocOfHome 1.4.2

Stand: 25. Juli 2026

## Zugriffsschutz

DocOfHome besitzt weiterhin keine Benutzeranmeldung und ist für ein
vertrauenswürdiges privates Netzwerk vorgesehen. Die Anwendung darf nicht ohne
zusätzlichen vorgeschalteten Zugriffsschutz öffentlich aus dem Internet
erreichbar sein.

## Projektlinks

Die GitHub-Verweise sind zentral in `backend/app/core/project_info.py`
vorbereitet. Solange das öffentliche Repository noch nicht existiert, bleiben
sie auf der Info-Seite verborgen.

## Feedback

- Das feste Ziel ist ein öffentlicher Nextcloud File Drop. Seine Erreichbarkeit
  kann erst beim tatsächlichen Upload geprüft werden.
- Der File Drop muss auf Nextcloud weiterhin bestehen und Uploads erlauben.
- Es gibt noch keine Anhänge, Screenshots oder lokale Warteschlange.
- Schlägt die Übertragung fehl, bleibt der Text im geöffneten Formular, wird
  aber nicht automatisch zwischengespeichert.
- Das Rate-Limit schützt die DocOfHome-API, kann aber direkte Zugriffe auf einen
  öffentlich bekannten File-Drop-Link nicht verhindern.

## Dashboard und Elektro-Dokumentation

Die bekannten Grenzen aus 1.4.1 für Serienablesung, nummerierte Einzelklemmen,
Aderlisten und normgerechte Elektro-CAD-Ausgabe bleiben bestehen.
