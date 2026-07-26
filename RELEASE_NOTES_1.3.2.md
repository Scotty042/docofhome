# DocOfHome 1.3.2

DocOfHome 1.3.2 korrigiert Mehrfacheinspeisungen an Phasenverteilerblöcken auf
bereits bestehenden Installationen.

## Ursache

Die ursprüngliche elektrische Topologie besaß einen eindeutigen Index auf
`target_kind` und `target_id`. Damit war je Ziel nur eine aktive Quelle möglich.
Migration `0027` entfernte diese Beschränkung in neuen Datenbanken. Auf Systemen,
die `0027` bereits mit einem älteren Stand ausgeführt hatten, wurde eine später
korrigierte historische Migration jedoch nicht erneut ausgeführt. Der alte
Index blieb deshalb erhalten, obwohl Anwendung und Tests Mehrfacheinspeisungen
unterstützten.

## Korrektur

Migration `0033_remove_legacy_single_target_topology_index` prüft die reale
Datenbank und entfernt den Index
`uq_electrical_connections_active_target`, falls er noch vorhanden ist.

Danach sind beispielsweise folgende Verbindungen gleichzeitig möglich:

```text
Zähler / Sunny Home Manager -> Phasenverteilerblock L1
PV-Wechselrichter           -> Phasenverteilerblock L1
Phasenverteilerblock L1     -> Unterverteilung / Sammelschiene
```

Die Eindeutigkeit des vollständigen Verbindungspaars bleibt erhalten. Dieselbe
Quelle kann also nicht versehentlich zweimal mit demselben Ziel verbunden
werden.

## Phasenlogik

Die bestehende Leiterprüfung bleibt aktiv:

- eine Komponente akzeptiert nur konfigurierte Leiter;
- ein Ausgang für L2 ist nur zulässig, wenn L2 mindestens einmal eingespeist ist;
- L1 wird nicht automatisch zu L2 oder L3 umgedeutet;
- mehrere Quellen dürfen denselben Leiter einspeisen.

## Update

Vor dem Update den persistenten Datenordner sichern. Beim Containerstart führt
Alembic Migration `0033` automatisch aus. Danach die zweite Einspeisung erneut
anlegen.
