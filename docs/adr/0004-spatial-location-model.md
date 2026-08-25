# ADR-0004: Single-home spatial Location model

- Status: Accepted
- Date: 2026-07-20

## Context

Electrical, network, document, maintenance, and smart-home modules need one shared representation of
the house, floors, rooms, outdoor areas, cabinets, and installation points. The Asset Engine already
owns hierarchical `Location` records and Asset references through `location_id`. Introducing
separate building and room tables would create competing location identities, duplicate hierarchy
rules, and make historical Asset assignments ambiguous.

JARVIS version 1 manages one installation and one house. Existing installations may already contain
arbitrary Location hierarchies created before typed spatial semantics exist. Their UUIDs, data,
relationships, and Asset references must survive the transition.

## Decision

- Keep Asset Engine `Location` as the only spatial entity and extend it additively with
  `location_type`, `short_name`, `sort_order`, and `notes`.
- Support the allow-listed types `building`, `floor`, `room`, `area`, `cabinet`,
  `installation_point`, and `outdoor`.
- Require exactly one active root per database. The root has type `building`; every other record has
  an active parent and cannot use `building`.
- Enforce the basic root/type invariant with a database check constraint and a partial unique index.
  Keep cycle, active-parent, move, and archive validation in `LocationService`, where transactions
  and understandable domain errors are available.
- Keep all hierarchy queries, derived breadcrumbs and paths, stable tree ordering, search, filters,
  pagination, and active Asset counts in `LocationRepository`.
- Derive paths from parent relationships on every read. Do not store a path string that could become
  stale after renaming or moving an ancestor.
- Create or initially rename the root with the installation name in the same transaction as
  first-run setup. Later settings edits do not overwrite a user-managed root name.
- Add migration `0006`. It backfills existing Locations as `area`, inserts one new `building` root,
  and reparents only previous top-level records. Existing Location UUIDs, subtrees, fields, archive
  state, and Asset `location_id` values remain unchanged.
- Prevent archiving the root or a Location with active direct children or non-deleted directly
  assigned Assets. Archived Locations remain readable and cannot receive new active assignments.
- Continue exposing the established `/api/v1/locations` CRUD contract, extended with tree, move,
  path, breadcrumb, type, and Asset-count data.

## Consequences

- Every current and future module can reference the same stable Location UUID without translating
  between building, room, and Asset Engine models.
- Garage, workshop, garden house, and outdoor structures can be represented beneath the single
  house without implying separate buildings or electrical distributions.
- Renaming or moving a Location updates every derived descendant path immediately and requires no
  path backfill.
- Repository path and descendant-count calculation reads the hierarchy as a snapshot. This favors
  correctness and simple SQLite operation for the intended single-home scale over premature graph
  caching.
- A future multi-building or tenant design requires a new ADR and additive contract; version 1 does
  not generalize the root into tenant ownership.
- Drag-and-drop and floor-plan editing can be added later without changing the persisted hierarchy
  or current API identities.
