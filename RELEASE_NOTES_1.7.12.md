# DocOfHome 1.7.12

`save_recipe` besitzt nun ein vollständiges MCP-Schema mit einzelnen Feldern für Titel,
Zutaten, Schritte, Kategorie, Tags, Zeiten, Portionen, Notizen, URLs und Anhänge. Dadurch
können MCP-Clients einen korrekten Werkzeugaufruf erzeugen, ohne ein unbeschriebenes
`payload`-Objekt konstruieren zu müssen.

Die MCP-Berechtigung der geprüften Installation war bereits `admin`; die Korrektur betrifft
daher ausschließlich den Werkzeugvertrag. Keine Datenbankmigration.
