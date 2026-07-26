# DocOfHome 1.4.2

DocOfHome 1.4.2 vereinfacht die Info-Seite für die geplante öffentliche
Veröffentlichung des Projekts.

## Info-Seite und Projektlinks

- Das konfigurierbare Impressum wurde vollständig aus Oberfläche und API
  entfernt.
- Projekt-, Repository-, Release- und Issue-Verweise werden nicht mehr pro
  Installation gepflegt. Sie liegen zentral im Quellcode und bleiben verborgen,
  solange das öffentliche GitHub-Repository noch nicht eingetragen ist.
- Die Lizenzinformation wird fest aus dem Projektstand angezeigt.

## Direkt aktives Feedback

Das Feedbackformular ist ohne zusätzliche Integration direkt aktiv. Das Backend
erzeugt pro Einsendung ein begrenztes ZIP mit:

- `feedback.md` für die lesbare Nachricht;
- `metadata.json` für strukturierte Angaben;
- `README.txt` mit dem übertragenen Umfang.

Das ZIP wird serverseitig an den fest hinterlegten öffentlichen Nextcloud File Drop übertragen. Datenbank, Integrationskonfiguration, Passwörter und Tokens
werden nicht aufgenommen. Browserkennung, Route, Fenstergröße und App-Version
werden weiterhin nur nach ausdrücklicher Zustimmung ergänzt.

## Datenmodell

Migration `0036_remove_configurable_about_fields` entfernt die mit 1.4.1
angelegten Projekt-, Impressums- und Feedback-Konfigurationsfelder. Gebäude-,
Asset-, Elektro-, Verbrauchs- und Integrationsdaten bleiben unverändert.

## Buildkorrekturen der Releasepakete

- `r2` stellt den versehentlich veränderten transitiven npm-Eintrag `rfdc`
  wieder auf die veröffentlichte Version `1.4.1` zurück.
- `r3` stellt die weiterhin benötigten Integrationsmetadaten und die allgemeine
  Pflichtfeldregel in `SettingsPage.vue` wieder her. Diese Hilfen werden von den
  unveränderten Home-Assistant-, Immich-, Nextcloud- und FRITZ!Box-Karten
  verwendet und waren beim Entfernen der pflegbaren About-Felder versehentlich
  mit entfernt worden.

