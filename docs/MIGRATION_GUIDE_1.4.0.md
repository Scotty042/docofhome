# Migration auf DocOfHome 1.4.0

1. Den persistenten DocOfHome-Datenordner vollständig sichern.
2. Das bisherige Quellverzeichnis durch den Inhalt von `DocOfHome-1.4.0.zip`
   ersetzen; eigene `compose.yaml`-Anpassungen vorher sichern und anschließend
   kontrolliert übernehmen.
3. Image neu bauen und Container starten.
4. Im Log prüfen, dass Alembic bis Revision `0034` aktualisiert.
5. Eine Verteilung öffnen und zuerst FI/RCD, N-Schiene und Sammelschiene
   zuordnen. Bestehende Geräte bleiben unverändert und können schrittweise
   ergänzt werden.

Migration `0034` fügt nur nullable Spalten, Indizes und Fremdschlüssel hinzu.
Ein Downgrade auf `0033` entfernt diese Zuordnungen wieder, ohne die bestehenden
Schutzgeräte oder Schrankkomponenten zu löschen.
