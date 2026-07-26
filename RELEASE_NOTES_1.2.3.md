# DocOfHome 1.2.3

DocOfHome 1.2.3 behebt einen TypeScript-Buildfehler aus 1.2.2.

## Korrektur

Nach erfolgreicher MDI-Prüfung brach `vue-tsc --noEmit` in
`frontend/src/services/immichGallery.test.ts` ab. Das dort verwendete
Konfigurationsobjekt entsprach nicht mehr `ConfigurationRead`, weil das in 1.2.0
ergänzte Pflichtfeld `online_product_image_search_enabled` fehlte.

Das Test-Fixture enthält dieses Feld nun explizit. Zusätzlich wurde der
Funktionsparameter von `selectedImmichAlbumId` auf
`Pick<ConfigurationRead, 'integrations'>` begrenzt. Die Funktion benötigt nur
die Integrationsliste und ist damit nicht länger unnötig an sämtliche
Konfigurationsfelder gekoppelt.

## Technische Auswirkungen

- keine Änderung an Backend, API oder Datenmodell;
- keine neue Datenbankmigration;
- Alembic-Head bleibt `0029`;
- bestehende Daten und Einstellungen bleiben unverändert.

## Update

Ein Update von 1.2.2 auf 1.2.3 erfordert den üblichen Image-Neubau und
Containerneustart. Vor dem Update bleibt ein vollständiges Backup empfohlen.
