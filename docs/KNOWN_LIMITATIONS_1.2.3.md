# Bekannte, nicht releasekritische Grenzen von DocOfHome 1.2.3

Stand: 24. Juli 2026

- DocOfHome besitzt weiterhin keine Benutzerverwaltung und gehört nur in ein
  vertrauenswürdiges privates Netzwerk.
- Die vollständigen Backend-, Frontend-, Docker- und HA-Lastprüfungen müssen in
  CI oder auf dem Zielsystem mit allen Abhängigkeiten ausgeführt werden.
- In der isolierten Releaseumgebung scheiterte die erneute npm-Installation an
  einem HTTP-503-Fehler des internen Paketdienstes. Deshalb wird der vollständige
  Vite-Build hier nicht als bestanden behauptet.
- Sprint 0039 bleibt ein nicht freigegebener Planungsentwurf.

Der konkret gemeldete TypeScript-Fehler in `immichGallery.test.ts` ist in 1.2.3
korrigiert. Details stehen in `PROJECT_HISTORY.md`.
