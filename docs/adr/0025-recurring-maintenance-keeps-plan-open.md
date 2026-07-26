# ADR-0025 – Wiederkehrende Wartungen bleiben als Plan offen

## Status

Accepted

## Entscheidung

Der Abschluss einer wiederkehrenden Wartung erzeugt ein unveränderliches Ereignis und verschiebt
die Fälligkeit auf den nächsten zukünftigen Termin. Der Wartungsplan bleibt offen. Einmalige
Aufgaben werden dagegen abgeschlossen.

## Folgen

- Ein Plan besitzt eine dauerhafte UUID und eine nachvollziehbare Erledigungshistorie.
- Verpasste Intervalle erzeugen nicht automatisch mehrere künstliche Ereignisse.
- Externe Benachrichtigungen bleiben außerhalb dieses Sprints.
