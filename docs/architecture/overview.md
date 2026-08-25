# Architecture overview

```text
Browser (Vue 3 / Vuetify)
        |
        | REST + WebSocket
        v
FastAPI application
        |
        +-- Versioned /api/v1 routes
        +-- Settings service (validation + transaction boundary)
        +-- Settings repositories (SQLModel sessions)
        +-- Asset services (validation + transaction boundaries)
        +-- Asset repositories (querying + soft-delete visibility)
        +-- Spatial Location service (hierarchy + archive transactions)
        +-- Spatial Location repository (tree + paths + Asset counts)
        +-- Electrical services (roles + hierarchy + position transactions)
        +-- Electrical repositories (Asset/Location projections + complete tree)
        +-- Home Assistant services (read-only snapshot + local visibility selection)
        +-- Home Assistant repositories (selection + Asset link persistence)
        +-- Immich connector (read-only metadata + bounded thumbnail proxy)
        +-- Immich link service/repository (local Asset gallery references)
        +-- Optional integration connectors
        +-- SQLite persistent database
        +-- Backup and migration services
```

The frontend never communicates directly with Home Assistant, Immich, Nextcloud, or Paperless. Connector credentials remain in the backend.

## First-run flow

The Vue router checks `GET /api/v1/setup/status` before entering the application shell. A database
without a completed application setting is sent to `/setup`. The final wizard action submits one
validated payload to the settings service, which stores general and integration settings, creates
or initially names the single building root, and marks setup complete in a single commit. Subsequent
starts enter the dashboard.

Settings are stored under `/data/database/jarvis.sqlite3`, which is mounted from the host. Alembic
owns schema evolution; application startup does not recreate or seed over settings. Integration
secrets never appear in read models. The frontend receives only `secret_configured` and sends a new
secret solely when the user explicitly enters one.

Status lookup failures are distinct from an incomplete setup: the router shows a retryable backend
unavailable state and enters the wizard only after a successful `completed=false` response.
Integration base URLs reject embedded URL userinfo. A separate non-secret `account` field can hold
an optional connector account identifier, while passwords, tokens, and API keys remain write-only.

## Asset Engine

The Asset Engine follows the same route-schema-service-repository separation as settings. Six
versioned resource families describe inventory, classification, placement, labels, and directional
relationships. Services validate references and own commits or rollbacks; repositories implement
stable pagination, case-insensitive search, allow-listed sorting, filters, and normal exclusion of
soft-deleted rows.

All records live in the persistent SQLite database under `/data`. Migration `0004` creates tables,
foreign keys, and query indexes without creating domain rows or modifying settings. The Vue asset
views consume only `/api/v1` and never access storage directly.

Migration `0005` additively backfills human-readable JARVIS codes and per-type counters without
replacing existing rows or UUIDs. New codes are allocated through an atomic counter update in the
same transaction as the asset. Application database connections enable SQLite foreign-key checking
on connect; service checks add soft-delete and cross-table product/type rules.

Asset replacement is a dedicated transaction rather than an edit: it retires the old row, inserts a
new row with a new UUID/code, and creates an immutable `replaced_by` relationship. The frontend uses
the same workflow from the asset detail and editor views, making the retained history visible without
controlling any external system.

## Spatial model

The spatial model extends the Asset Engine `Location` record rather than introducing separate
building or room identities. One active `building` root represents the configured house. Typed
floors, rooms, areas, cabinets, installation points, and outdoor locations form an acyclic
parent-child tree below it. Assets continue to reference the same stable Location UUID through
`location_id`.

`LocationService` owns root, parent, cycle, move, and archive rules. `LocationRepository` owns the
hierarchy snapshot, derived paths and breadcrumbs, tree ordering, search, filters, pagination, and
direct/descendant Asset counts. The API exposes these values below `/api/v1/locations`; no redundant
path string is stored in SQLite.

Migration `0006` adds the typed spatial fields and creates the single building root. Previous
top-level Locations are attached beneath it while every pre-existing UUID, subtree, archive state,
and Asset reference remains unchanged. The responsive Vue interface presents an expandable desktop
tree and hierarchical mobile cards from the same API data.

## Electrical distributions

The electrical module adds roles to existing Assets instead of creating a second inventory or
location model. `electrical_components` owns the stable role UUID, lifecycle, and one-active-role
constraint. One-to-one distribution and protective-device tables store only electrical fields.
Asset name, immutable JARVIS code, status, and derived Location path are joined for API reads and are
never copied into the electrical schema.

`ElectricalDistributionService` owns main/sub hierarchy, cycle-safe moves, Asset eligibility, and
archive protection. `ElectricalProtectiveDeviceService` owns the common Location requirement,
complete-or-unknown positions, capacity bounds, non-overlapping module intervals, and transactions.
Repositories provide historical reads, stable pagination, search, filters, allow-listed sorting,
complete trees, counts, and paginated Asset candidates below `/api/v1/electrical`.

Migration `0007` creates only the electrical role and detail tables. It has no seed or backfill and
does not update existing Asset, Location, setting, relationship, or UUID data. The responsive Vue
interface consumes the full tree and every advertised Asset-selection page; route-aware state guards
prevent older requests from replacing a newly selected distribution or editor record.

## Home Assistant visibility selection

The Home Assistant connector reads complete device, entity, area, and state snapshots and remains
strictly read-only. `HomeAssistantService` combines that external snapshot with local state from
`HomeAssistantSelectionRepository`; no selection value is written back to Home Assistant. Absence
of a selection setting means `all`, preserving the behavior of upgraded installations.

`home_assistant_selection_settings` stores the singleton mode and
`home_assistant_entity_selections` stores normalized entity IDs. The selection service validates
and replaces both atomically. Migration `0011` creates these tables without seeding or modifying
existing Home Assistant Asset links. Stored IDs survive temporary absence from an external
snapshot, and hiding an entity never deletes its Asset assignment.

Normal device and entity reads use `selection_scope=visible`; the selection dialog requests
`selection_scope=all` and follows every response page. In `selected` mode, visible devices are
derived from currently visible selected entities. Existing summary totals remain complete-snapshot
totals, while additive fields expose visible counts and the active local selection mode.

## Immich gallery links

Immich remains the owner of image binaries. The server-side `ImmichConnector` uses the stored API
key for stable metadata search, asset reads, and thumbnail reads only. Requests have a fixed timeout,
do not follow redirects, and never expose credentials or the private integration URL to Vue. The
same-origin thumbnail endpoint accepts only allow-listed raster media types and bounded response
sizes.

`ImmichService` verifies active Tectoryn Assets and current Immich image identity before creating a
link. `ImmichLinkRepository` persists the explicit association and a small filename, timestamp,
dimension, and favorite snapshot in `immich_asset_links`. Local list and unlink operations require
no external request, so users retain context and control during an Immich outage. Archived Assets
keep historical links but reject new ones.

Migration `0012` adds only the link table, uniqueness/validity constraints, foreign key, and query
indexes. It neither seeds links nor changes existing Asset, Home Assistant, setting, or integration
records. The Asset detail consumes only `/api/v1/immich`; it never accesses Immich directly.

## Knowledge, notes, and local target identity

Wiki pages and object notes are owned by the local SQLite database. `wiki_pages` forms an acyclic
parent-child hierarchy with stable UUIDs and server-generated slugs; display paths are derived and
never stored redundantly. `domain_notes` uses the same allow-listed target types as local document
links. Services resolve each UUID against the canonical Asset, Location, distribution, protective
device, or circuit model before allowing a write. Electrical archive state is taken from the shared
`electrical_components` lifecycle row, so archived distributions and protective devices remain
readable but cannot receive new notes.

The Vue Wiki and note cards communicate only with `/api/v1/wiki/pages` and `/api/v1/notes`. Wiki
content is plain text in this sprint; no HTML from users is rendered. Wiki search is part of the
bounded global search response and returns only local application routes.

## Tasks and recurring maintenance

`work_items` stores both one-off tasks and recurring maintenance plans. Optional target references
reuse the same stable local UUID contract as notes. The service owns all state transitions and writes
immutable completion, cancellation, and reopening entries to `work_item_events`. Completing a
recurring maintenance plan advances its due date until it is in the future while keeping the plan
open; completing a one-off task closes it. Database constraints mirror the API rules for recurrence
type, due date, and bounded interval.

The frontend exposes a central `/maintenance` view, target-bound cards, and summary counts on the
dashboard. Reminders remain in-app status information; the backend does not send mail, push messages,
or commands to external systems.

## Advisory documentation quality

Quality checks create immutable `quality_runs` and `quality_issues` snapshots. Rules inspect local
records and may verify existing document links through the already root-scoped server-side Nextcloud
document service. A temporary Nextcloud listing failure does not label every linked document as
broken. Checks never modify domain records, and generated routes are fixed local application paths.

The lightweight scheduler starts only after first-run setup is complete and creates at most one
scheduled report within 24 hours. The service retains the latest 30 runs. Manual runs and the latest
persisted report are exposed below `/api/v1/quality`; Vue displays the score, severity counts, filters,
and safe navigation to the affected local record.

## Photovoltaic energy balance

The energy module deliberately reuses cumulative consumption meters. The singleton
`energy_configurations` row references one active kWh meter each for grid import,
PV generation, and grid export. `EnergyService` delegates period calculation to the
existing consumption service and derives house consumption, self-consumption,
autonomy, and self-consumption rate at request time. Derived monthly results are not
persisted.

`energy_components` documents PV sources, inverters, and storage units and may
reference an existing Asset. Inventory identity, location, images, documents, and
lifecycle therefore remain owned by the Asset Engine.

Electrical supply topology is a directed acyclic graph rather than a strict tree from
migration `0027` onward. Multiple distinct sources may feed the same target. The
service still prevents cycles and duplicate source-target pairs, derives all reachable
root source names, and returns the union of incoming phases. The Vue projection shows
each shared target once while exposing all incoming connections on that row.
