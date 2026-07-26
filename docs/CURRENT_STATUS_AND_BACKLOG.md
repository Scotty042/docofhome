# DocOfHome – aktueller Status und Backlog

Stand: 25. Juli 2026  
Aktuelles Release: `1.4.2`  
Aktueller Alembic-Head: `0036`

## Release 1.4.2 – veröffentlichungsfähige Info- und Feedbackfunktion

Unter **Mehr → Über DocOfHome** stehen Projektinformationen, die installierte
Version, ausgelieferte Release Notes und ein direkt aktives Feedbackformular
bereit.

Projekt- und spätere GitHub-Verweise werden zentral im Quellcode gepflegt. Ein
konfigurierbares Impressum gehört nicht mehr zum Produkt. Feedback wird vom
Backend als begrenztes ZIP an den fest hinterlegten öffentlichen Nextcloud File
Drop übertragen. Technische Angaben werden nur nach sichtbarer Zustimmung
aufgenommen.

Der Dashboard-Button **Zählerstände erfassen** öffnet weiterhin direkt den
mobilen Ablesedialog.

## Verbindlicher Ausgangsstand

DocOfHome 1.4.2 baut auf 1.4.1 auf. Der Elektro-Funktionsstand mit
Sammelschienen, FI-Gruppen, Neutralleiterschienen, TE-Raster und Drag-and-drop
bleibt unverändert erhalten.

Migration `0036` entfernt ausschließlich die nicht mehr benötigten
konfigurierbaren Projekt-, Impressums- und Feedbackfelder. Die
Docker-/Compose-Architektur bleibt unverändert.

## Aktiver Entwicklungsstatus

- Aktiver freigegebener Sprint: **keiner**
- Aktiver Implementierungsauftrag: **keiner**
- Zuletzt abgeschlossener Sprint: **0039, mit 1.4.2 vereinfacht**
- Nächste Versionsnummer: noch nicht beschlossen

## Unnummerierter Produkt-Backlog

1. optionale Authentifizierung und Mehrbenutzerrollen;
2. optional aktivierte read-only Workload-Erkennung;
3. getrennte Speicher-Lade-/Entladeflüsse und Leistungskurven;
4. erweiterte Druck- und Berichtsvorlagen;
5. zusätzliche versionierte Importadapter.

## Qualitätsgates für 1.4.2

Vor dem produktiven Rollout sind auf Zielsystem oder CI zusätzlich erforderlich:

- vollständiger Frontend-Build mit `npm ci`, Vitest, `vue-tsc` und Vite;
- vollständiger Backend-Lauf mit Ruff, mypy und Pytest;
- Docker-Image-Build und Containerstart;
- Update einer Datenbankkopie bis `0036`;
- praktischer Testupload in den fest hinterlegten öffentlichen File Drop.

Nicht ausgeführte Prüfungen werden im Validierungsbericht ausdrücklich als offen
ausgewiesen.
