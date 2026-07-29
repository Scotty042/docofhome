# Implementation Summary 1.7.4.7

`CabinetWiringOverlay.vue` kann nun sowohl die vollständige Hauptverkabelung als auch einen interaktiven Fokusmodus darstellen.

## Umsetzung

- optionale Overlay-Eigenschaft `interactive`;
- delegierte Pointer- und Klick-Ereignisse auf den vorhandenen `data-electrical-endpoint-key`-Elementen;
- direkter Verbindungsfilter anhand des gewählten Endpunkts;
- Mouse-over für temporäre Auswahl, Klick/Antippen für Fixierung und Escape zum Zurücksetzen;
- dynamische Hervorhebung des gewählten Endpunkts und seiner direkten Nachbarn;
- selektive Anzeige eines automatischen Kammschienenkontakts nur beim Fokus auf die betreffende Sicherung;
- unveränderter vollständiger Verkabelungsmodus bei deaktivierter Interaktion.
