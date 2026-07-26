# Sprint 0011: Read-only Immich gallery links

- Status: Approved
- Target branch: `feature/immich-gallery-links`
- Depends on: Sprint 0010, migration `0011`, ADR-0006 and ADR-0009

> This document is the complete implementation contract for this sprint. The binding rules in
> `docs/DEVELOPMENT_GUIDELINES.md` apply in addition.

## Goal

Users can browse images from a configured Immich instance and explicitly link them to docofhome
Assets. Asset details display the linked image gallery without exposing the Immich API key to the
browser. docofhome remains usable when Immich is disabled or unavailable and never writes to Immich.

## Context

Immich is already optional configuration and its API key can be tested server-side. The official
Immich API exposes stable metadata search (`POST /search/metadata`), asset detail
(`GET /assets/{id}`), and thumbnail (`GET /assets/{id}/thumbnail`) endpoints. API keys support
scoped `asset.read` and `asset.view` permissions. docofhome therefore needs no upload, album mutation,
shared-link, or administrative permission for this sprint.

## Requirements

- The frontend communicates only with docofhome `/api/v1`; the Immich API key never reaches the
  browser, URLs, logs, errors, image sources, or response metadata.
- All Immich calls are server-side, read-only, have a ten-second timeout, reject redirects, and use
  the stored enabled integration URL and API key.
- Only Immich images are browsed and linked. Video, audio, original downloads, upload, deletion,
  editing, album mutation, tagging, and shared-link creation are excluded.
- A link is an explicit local user decision between one docofhome Asset UUID and one Immich asset
  UUID. The same pair is unique; one image may be linked to multiple docofhome Assets.
- Link creation verifies the current docofhome Asset and Immich image and stores a small immutable
  metadata snapshot: original filename, capture timestamp, dimensions, and favorite flag.
- Immich disappearance never deletes a link or its metadata snapshot. Local unlinking remains
  possible without contacting Immich.
- New links to archived docofhome Assets are rejected. Existing links remain readable on archived
  Asset details.
- Core Asset CRUD and every non-Immich module work normally without Immich.

## Backend

### Persistence

- `immich_asset_links` stores UUID `id`, `asset_id`, `immich_asset_id`, snapshot fields,
  `created_at`, and `updated_at`.
- A database unique constraint protects `(asset_id, immich_asset_id)`.
- Foreign keys reference the existing Asset identity. No Asset, setting, integration secret,
  Home Assistant link, or external record is changed by migration or linking.
- Links are association records and may be physically deleted by an explicit unlink action. Assets
  themselves retain their existing soft-delete lifecycle.

### Connector and API

- `ImmichConnector` owns HTTP construction, authentication, timeout, redirect rejection, safe
  response parsing, and secret-free integration errors.
- `ImmichLinkRepository` owns local link queries and writes.
- `ImmichService` owns configuration checks, external image verification, link validation, and
  transaction boundaries.
- `GET /api/v1/immich/assets` browses paginated image candidates with newest-first ordering,
  optional filename search, and optional album UUID filter.
- `GET /api/v1/immich/assets/{immich_asset_id}/thumbnail` proxies a bounded safe raster thumbnail
  with a private short-lived cache header.
- `GET /api/v1/immich/links?asset_id=...` reads only local stored links.
- `POST /api/v1/immich/links` verifies and creates a link atomically.
- `DELETE /api/v1/immich/links/{link_id}` removes only the local link.
- Configuration failures map to HTTP 409, external connection/timeout failures to 502, missing
  local or external records to 404, invalid/conflicting links to 409 or 422.

## Frontend

- Asset detail includes an `Immich-Fotos` card showing linked thumbnails, filenames, timestamps,
  loading, empty, unavailable, and image-fallback states.
- Active Assets expose `Fotos verknüpfen`; archived Assets remain read-only.
- The responsive dialog browses remote images page by page, supports filename search, shows the
  selected count, prevents duplicate linking, and permits several links without losing dialog state.
- Linked thumbnails use only the local docofhome proxy URL. The configured Immich URL and key do not
  appear in frontend state or markup.
- Unlink requires an explicit user action, updates the gallery immediately, and does not alter
  Immich.
- Mobile and desktop layouts work in Dark and Light Mode; filenames wrap and actions remain usable.

## Migration

- Migration `0012` follows `0011` and creates only `immich_asset_links` plus constraints and indexes.
- It contains no seed, external call, or data rewrite.
- Fresh upgrade, upgrade from `0011` with existing Assets and Home Assistant data, downgrade to
  `0011`, Alembic check, and `PRAGMA foreign_key_check` must pass without changing existing UUIDs or
  user values.

## Tests

- Connector tests verify API base normalization, `x-api-key`, endpoint methods and bodies,
  pagination, filename/album filters, timeout, redirect/status handling, safe JSON validation,
  thumbnail media allow-list, and size bound.
- Service/repository/API tests cover disabled/missing configuration, verified creation, unique
  pairs, archived Assets, persistence, local listing and offline unlink.
- Migration tests preserve existing Asset, Home Assistant selection, and Asset-link data.
- Frontend transport tests cover browse, link, unlink, thumbnail proxy paths, query serialization,
  and secret absence.
- Frontend presentation tests cover duplicate detection, responsive gallery metadata, and page
  replacement without losing already linked IDs.
- Ruff, mypy, pytest, Alembic upgrade/check, Vitest, vue-tsc, Vite, and Docker build are green.

## Definition of Done

- [ ] Every contract in this sprint is implemented without out-of-scope Immich writes.
- [ ] API key and private integration URL remain backend-only and secret-free in errors.
- [ ] Migration `0012` is additive and update-safe.
- [ ] Browse, thumbnail proxy, link, offline list/unlink, errors, and pagination are tested.
- [ ] Asset detail is responsive and understandable in all required states.
- [ ] Existing Asset and Home Assistant data remain unchanged.
- [ ] All backend, frontend, migration, and Docker quality gates are green.
- [ ] README, CHANGELOG, ADR, architecture overview, and sprint status are current.
- [ ] The pull request contains no private URLs, credentials, or generated user data.

## Acceptance criteria

1. With a read-only Immich API key, an active Asset can browse and link an image without any Immich
   write request.
2. The linked thumbnail appears through a same-origin docofhome URL and no credential reaches the
   browser.
3. More than one image can be linked, while the same Asset/image pair cannot be duplicated.
4. When Immich is unavailable, the saved filename and timestamp remain visible and the link can be
   removed locally.
5. Archived Assets show historical links but cannot receive new ones.
6. Existing installations update without new rows or changes to prior data.

## Out of scope

- Immich upload, delete, edit, favorite, tag, album, sharing, original download, or video playback.
- Automatic synchronization, scheduled caching, local image copies, OCR, face/person, or smart
  semantic search.
- Product images, Location galleries, electrical galleries, Nextcloud documents, or Home Assistant
  media.
