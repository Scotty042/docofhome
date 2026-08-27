# Validierung DocOfHome 1.7.12

- Laufende MCP-Einstellung geprüft: aktiviert, Token vorhanden, Berechtigung `admin`.
- Generisches Rezept-Payload durch explizite typisierte MCP-Parameter ersetzt.
- Such- und Speicherverträge für Rezepte statisch geprüft.
- Python-Syntax, Version, Branding und Releasevertrag geprüft.
- Release-ZIP mit `unzip -t` geprüft und SHA-256 ermittelt.

Ein realer MCP-Schreibtest benötigt die neu bereitgestellte Zielversion und wird nach dem
Deployment empfohlen. Vollständige CI-/Docker-Tests bleiben erforderlich.
