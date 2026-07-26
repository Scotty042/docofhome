# ADR-0029 – Die Elektro-Topologie ist ein Mehrquellen-DAG

## Status

Accepted; supersedes ADR-0020 hinsichtlich der Ein-Quellen-Beschränkung

## Kontext

ADR-0020 modellierte die Versorgung als gerichteten Baum und erlaubte pro Ziel
nur eine eingehende Verbindung. Ein Gebäude mit Netzanschluss, PV-Wechselrichter,
Speicher oder Ersatzversorgung besitzt jedoch legitime Knoten, die von mehreren
Energiequellen gespeist werden. Eine künstliche Zwischenkomponente würde diese
fachliche Realität verschleiern.

## Entscheidung

Die Topologie bleibt gerichtet und azyklisch, wird aber als DAG statt als Baum
behandelt. Ein Ziel darf mehrere eingehende Verbindungen besitzen. Verboten
bleiben:

- Selbstverbindungen;
- Zyklen;
- eine zweite aktive Verbindung mit demselben Quell- und Zielpaar;
- Verweise auf fehlende oder archivierte Endpunkte.

Die API leitet für jeden Knoten alle erreichbaren Wurzelquellen und die
Vereinigung der eingehenden Phasen ab. Die Oberfläche zeigt sämtliche
Einspeisungen des Knotens und bietet jede Verbindung separat zum Bearbeiten oder
Entfernen an.

Für passive Schrankkomponenten wird die Leiterführung zusätzlich validiert. Die
Phasenliste einer Verbindung bezeichnet denselben Leiter an Quelle und Ziel; es
gibt keine implizite Umbenennung von L1 nach L2. Ein Ausgang darf nur Leiter
führen, die an der Komponente konfiguriert und über mindestens eine aktive
Einspeisung vorhanden sind. Änderungen oder Löschungen von Einspeisungen dürfen
bestehende Abgänge nicht unversorgt zurücklassen.

## Folgen

- Netz, PV, Speicher und weitere dokumentierte Quellen können gemeinsam auf
  Sammelschienen oder Verteilungen wirken;
- vorhandene Verbindungen bleiben unverändert;
- eine hierarchische Darstellung zeigt einen gemeinsam versorgten Knoten nur
  einmal, listet dort aber alle eingehenden Verbindungen und Quellnamen;
- ein technischer Downgrade auf die frühere Unique-Regel setzt voraus, dass pro
  Ziel zuvor höchstens eine aktive Einspeisung verbleibt.
