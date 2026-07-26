# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.2.4

Stand: 24. Juli 2026

- DocOfHome besitzt weiterhin keine Benutzerverwaltung und gehört nur in ein
  vertrauenswürdiges privates Netzwerk.
- Der Browser-Fallback der Online-Produktbildsuche kann nur helfen, wenn der
  verwendete Browser Wikimedia erreichen darf. Sind sowohl Container als auch
  Browser blockiert, wird eine verständliche Fehlermeldung angezeigt.
- Ein Downgrade von `0030` auf `0029` setzt strukturierte Unterverteilungen auf
  den Reihenmodus zurück. Feld- und Bereichsdaten bleiben erhalten, sind unter
  `0029` aber nicht nutzbar.
- Die vollständigen Backend-, Frontend- und Docker-Prüfungen benötigen eine
  Umgebung mit installierbaren Abhängigkeiten und Docker. Der genaue in dieser
  Releaseumgebung ausgeführte Umfang steht im Validierungsbericht.
- Sprint 0039 bleibt ein nicht freigegebener Planungsentwurf.
