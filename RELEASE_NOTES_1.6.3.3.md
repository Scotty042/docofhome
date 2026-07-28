# DocOfHome 1.6.3.4 – Explizite Kammschienen-Kontaktsynchronisation

## Behoben

- Phasen-/Kammschienen verwenden nach dem Speichern einen eigenen Synchronisations-Endpunkt.
- Die Verteilerschrankansicht übermittelt die tatsächlich sichtbaren Schutzgeräte-IDs ohne fragile Frontend-Filter auf optionale Bestandsfelder.
- Das Backend lädt jedes gemeldete Schutzgerät direkt aus Schutzgeräte-, Komponenten- und Asset-Tabelle und validiert Verteilung, Bereich, Reihe und vollständige TE-Überdeckung.
- Für jedes passende Schutzgerät wird verbindlich eine schreibgeschützte Verbindung **Phasen-/Kammschiene → Schutzgerät** mit automatisch berechneter Phase erzeugt.
- Kann kein sichtbares Schutzgerät zugeordnet werden, erscheint ein konkreter Diagnosefehler statt einer irreführenden Erfolgsmeldung mit `0 Schutzgerät(en)`.
- Scheitert die Kontaktsynchronisation nach dem erstmaligen Anlegen, bleibt der Dialog im Bearbeitungsmodus und erzeugt beim erneuten Speichern keine doppelte Schiene.

## Datenbank

Keine neue Migration erforderlich. Alembic-Head bleibt `0044`.
