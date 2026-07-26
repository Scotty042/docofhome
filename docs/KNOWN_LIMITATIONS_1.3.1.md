# Bekannte Grenzen von DocOfHome 1.3.1

- Drag-and-drop nutzt die HTML5-Desktopfunktion und wird auf breiten Ansichten
  angeboten. Auf Touchgeräten erfolgt die Platzierung weiterhin über den
  Positionsdialog.
- Passive Schrankkomponenten werden weiterhin über ihren Dialog positioniert
  und noch nicht selbst per Drag-and-drop verschoben.
- Passive Komponenten besitzen noch keine einzeln nummerierten Anschlussklemmen.
  Ein- und Abgänge werden als Verbindungen mit Leiterangabe dokumentiert.
- Die strenge Prüfung der verfügbaren Leiter ist derzeit für passive
  Schrankkomponenten möglich, da dort L1/L2/L3/N/PE explizit konfiguriert werden.
  Allgemeine Assets besitzen noch keine eigene Anschluss- oder Phasenmatrix.
- Bereits vorhandene Schutzgeräte können aus Kompatibilitätsgründen ihre bisher
  gespeicherte Rollenbreite weiterverwenden. Für neue Geräte sollte die Breite
  am Asset oder Asset-Typ gepflegt werden.
- Eine einzelne erste Zählerablesung reicht nicht zur Verbrauchsberechnung aus.
  Für einen Verbrauchswert werden weiterhin mindestens zwei verwertbare
  Zählerstände benötigt.
- DocOfHome besitzt keine Benutzerverwaltung und darf nur in einem
  vertrauenswürdigen privaten Netzwerk betrieben werden.
