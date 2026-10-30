# Kompaktes Design 1.9.2

Diese Version verdichtet das Salbei-Design aus 1.9.1 auf Wunsch des Nutzers. Allgemeine Haupttitel sind auf dem Desktop ungefähr 32 statt bis zu 48 Pixel groß. Die Kopfzeile ist 56 statt 72 Pixel hoch, die Seitenleiste 240 statt 274 Pixel breit. Karten, Listen, Formulare und Tabellen verwenden weniger Abstand. Dashboard und Gerätedetails sind ebenfalls angepasst. Auf Geräten mit Touch-Eingabe bzw. kleinen Bildschirmen bleiben Schaltflächen mindestens 44 Pixel hoch.

Es gibt keine Änderung an den gespeicherten Einstellungen, Zugangsdaten, Fachfunktionen oder Backendabläufen. Das Paket enthält keine Datenbank oder Testkonfiguration. Die beiden lokalen Vorschauinstanzen verwenden separate Beispieldaten und sind nicht die NAS-Installation. Die Integrationsschalter im Dichtevergleich werden allein im Browser mit Beispieldaten dargestellt; es werden dabei keine Einstellungen gespeichert und keine externen Dienste aufgerufen.

Der Umstieg folgt demselben GitHub-/Docker-Ablauf wie bisher, mit eigenem Release-Tag `v1.9.2`. Bestehende Docker-Umgebung, Netzwerke, Datenordner und Umgebungsvariablen beibehalten. Vor dem späteren Update ein vollständiges Backup anlegen. Gegenüber 1.9.1 gibt es keine neue Datenbankmigration (Head 0061).

Die lokale Prüfung ist in `../design-qa.md` dokumentiert. Die bekannten Backend-Testgrenzen aus 1.9.1 bleiben bestehen; `full_quality_gate_passed` bleibt false. Die laufende NAS-Installation wurde nicht geändert.
