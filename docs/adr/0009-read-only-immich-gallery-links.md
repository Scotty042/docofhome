# ADR-0009: Read-only Immich gallery links

- Status: Accepted
- Date: 2026-07-21

## Context

docofhome needs durable photo references for Assets while Immich remains the owner of image files.
Sending the API key to the browser would expose a reusable credential and create CORS and private
network coupling. Copying image binaries into SQLite would duplicate storage and create an
unspecified synchronization and retention lifecycle. Storing only an external UUID would make the
local Asset history unintelligible whenever Immich is unavailable.

The current official Immich API marks metadata search, asset detail, and thumbnail endpoints stable
and supports scoped API keys. The thumbnail endpoint can serve binary content and must therefore be
treated as an untrusted external response.

## Decision

- Immich remains the sole owner of image files; docofhome never uploads, edits, or deletes them.
- The backend is the only Immich client and authenticates with the stored `x-api-key` header.
- docofhome stores explicit Asset/image links plus a small metadata snapshot, not image binaries.
- A same-origin backend endpoint proxies thumbnails. It rejects redirects, non-allow-listed raster
  media types, and responses above the configured bound; the API key never enters a URL.
- Link creation performs a current Immich asset read and accepts only `IMAGE` records.
- Link listing and deletion are local operations so they remain available during an Immich outage.
- External absence does not delete, rewrite, or invalidate a local link automatically.
- The pair `(asset_id, immich_asset_id)` is unique. Links are removable association records and do
  not alter the Asset soft-delete lifecycle.

## Consequences

- Asset history retains useful filename and capture metadata while Immich is offline.
- Thumbnails require live Immich availability and are not offline image copies.
- API keys need only `asset.read` and `asset.view`; no write permission is required by docofhome.
- The proxy adds bounded backend traffic but prevents browser credential exposure and private URL
  leakage.
- Metadata snapshots can become stale after external edits; automatic refresh is deliberately a
  future sprint.
- Future galleries for Products, Locations, or other modules can reuse the connector but require
  their own explicit persistence and UI contracts.
