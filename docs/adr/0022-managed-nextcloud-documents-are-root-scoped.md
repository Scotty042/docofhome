# ADR-0022 – Verwaltete Nextcloud-Dokumente bleiben auf einen Stammordner begrenzt

## Status

Akzeptiert.

## Kontext

`docofhome` benötigt eine allgemeine Dokumentenablage, während Nextcloud Eigentümer der Dateien
bleiben soll. Eine uneingeschränkte WebDAV-Navigation über das gesamte Benutzerkonto würde das
Risiko unbeabsichtigter Änderungen erhöhen. Eine lokale Kopie aller Dateien würde dagegen
Datenbesitz, Speicherbedarf, Versionshistorie und Synchronisation duplizieren.

## Entscheidung

Die Nextcloud-Integration erhält einen relativen Dokumenten-Stammordner. Sämtliche Dokumentenpfade
werden serverseitig normalisiert, URL-kodiert und auf diesen Stammordner begrenzt. Die Dokumentenseite kommuniziert ausschließlich mit der lokalen `docofhome`-API und erhält weder
Nextcloud-URL noch Konto oder Secret. Die bestehende Einstellungsseite darf URL und Konto zur
Bearbeitung anzeigen; das gespeicherte Secret wird weiterhin ausschließlich im Backend gehalten.

Dateien bleiben vollständig in Nextcloud. SQLite speichert in Sprint 0027 nur die Konfiguration des
Stammordners, keine Datei- oder Ordnerkopien. Schreiboperationen erfolgen ausschließlich nach einer
sichtbaren Benutzeraktion. Uploads überschreiben nicht automatisch, Moves verwenden
`Overwrite: F`, und nur leere Ordner dürfen gelöscht werden.

## Folgen

- Nextcloud bleibt Daten- und möglicher Versionsinhaber der Dokumentdateien.
- Der lokale Kernbetrieb bleibt ohne Nextcloud verfügbar.
- Ein kompromittierter oder fehlerhafter Frontendpfad kann nicht außerhalb des Stammordners
  navigieren.
- Änderungen des konfigurierten Stammordners verschieben vorhandene Dateien nicht automatisch.
- Nextcloud-Dateiversionen können beim ausdrücklichen Ersetzen entstehen, werden in diesem Sprint
  aber nicht angezeigt oder verwaltet.
- Dokumentverknüpfungen benötigen in einem späteren Sprint lokale, stabile Referenzmetadaten und
  dürfen nicht durch unkontrollierte Remote-Pfade ersetzt werden.
