# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.1.1

- DocOfHome besitzt weiterhin keine Benutzerkonten oder Rollen und ist nur für
  ein vertrauenswürdiges privates Netzwerk vorgesehen.
- Die Energiebilanz basiert auf kumulativen kWh-Zählern. Fehlende Ablesungen an
  Monatsgrenzen werden als unvollständig beziehungsweise geschätzt markiert.
- Die Standardformel verwendet Netzbezug, gesamte PV-Erzeugung und
  Netzeinspeisung. Separate Speicher-Lade-/Entladeflüsse und zeitlich
  aufgelöste Leistungswerte sind in 1.1.1 keine eigenen Bilanzgrößen.
- Korrekturen historischer Zählerstände verändern folgerichtig die daraus
  abgeleiteten historischen Bilanzwerte.
- Die Elektro-Topologie dokumentiert Verbindungen, prüft aber keine reale
  Lastflussrechnung, Selektivität oder normgerechte Auslegung.
- Die visuelle Immich-Auswahl zeigt die ersten 36 Treffer der aktuellen Suche.
  Immich bleibt optional und read-only; ohne erreichbare Integration kann eine
  Ablesung weiterhin ohne Foto gespeichert werden.
- FRITZ!Box liefert je nach Modell, FRITZ!OS und Rechten nicht alle optionalen
  Hostattribute. Manuelle Dokumentation bleibt führend.
- Ein vollständiger Docker-Build und die dependency-basierten Testläufe müssen
  auf dem Zielsystem beziehungsweise in CI mit den im Lockfile festgelegten
  Paketen ausgeführt werden.
