# Sprint 0003: Electrical foundation

- Status: Draft / Planning only
- Target branch: `feature/electrical-foundation`
- Depends on: Asset Engine and ADR-0003

> This file plans the future electrical module. This documentation sprint does not authorize or
> contain application code, database migrations, generated schemas, or UI implementation.

## Ziel

Plan a complete offline-first electrical documentation module that maps a building's electrical
infrastructure from rooms and distributions through protective devices, circuits, cables, connected
devices, media, external references, replacements, and historical archival.

The later implementation must allow a person to understand what supplies and protects a device,
where components are installed, which cable and circuit connect them, and how the installation
changed over time without controlling the electrical system or Home Assistant.

## Hintergrund

The Asset Engine provides stable asset UUIDs, immutable JARVIS codes, locations, labels,
relationships, replacements, and archival foundations. The electrical module will add a structured
electrical view without duplicating generic assets or replacing their identities.

Electrical documentation is safety-relevant but JARVIS is not a planning, certification, or control
system. The module records user-supplied facts and media. It must clearly distinguish documented,
unknown, virtual, archived, and externally associated information.

## Anforderungen

### Gebäude und Räume

- A building is the top-level scope for an electrical installation.
- A building has a stable UUID, name, optional description, address-free display label, timestamps,
  and soft-delete state.
- Rooms belong to exactly one building and may reference an Asset Engine location where appropriate.
- Rooms have stable UUIDs and may be hierarchically grouped by floor or area without duplicating the
  generic location tree.
- Archived buildings and rooms remain readable but cannot receive new active electrical assignments.

### Unterverteilungen

- A distribution board belongs to one building and may be located in one room.
- It is represented by or linked to an Asset Engine asset rather than duplicating asset identity.
- It records a display name, optional designation, optional parent feed, row/slot metadata, and
  notes.
- Main and sub-distributions may form an acyclic supply hierarchy.
- The detail view must show installed protective devices, outgoing circuits, incoming feed, photos,
  documents, and archived/replaced components.

### Sicherungen und Schutzgeräte

- Protective devices are assets installed in a distribution board with an explicit position.
- Supported classifications include fuse, FI, RCD, LS, combined RCD/LS where needed, and surge
  protection.
- FI is treated as the German user-facing term for an RCD; the persisted technical type remains
  unambiguous and filterable.
- LS represents a miniature circuit breaker classification.
- RCD records may document rated current, residual current, pole count, and type when known.
- LS records may document rated current, characteristic, breaking capacity, and pole count when
  known.
- Fuses may document system/type, rated current, and physical size when known.
- Surge-protection devices may document class/type, poles, status notes, and upstream protection
  when known.
- Unknown technical values remain nullable; the UI must not invent defaults that look measured or
  certified.
- One RCD may protect multiple downstream LS devices or circuits through explicit relationships.

### Geräte

- Electrical devices reference existing Asset Engine assets and retain their UUIDs and JARVIS codes.
- A device may be connected to one or more physical or virtual circuits with a documented role.
- The module must not duplicate generic product, label, location, replacement, or asset archive data.
- Replacement uses the Asset Engine replacement workflow so the old and new device remain linked and
  historically readable.

### Stromkreise

- A circuit has a stable UUID, human-readable designation, building, source distribution, status,
  purpose, and optional notes.
- A physical circuit references its protecting device or protection chain and may reference one or
  more cables and connected assets.
- Circuit relationships express supply, protection, continuation, shared neutral, device connection,
  or other approved typed semantics without free-form structural ambiguity.
- Supply relationships must not contain cycles.
- Archived circuits remain readable and keep their devices, cables, protection, media, and history.

### Virtuelle Stromkreise

- A virtual circuit is explicitly marked and never presented as a physical cable run.
- It may group devices for documentation, monitoring, tenant, energy, or logical-zone purposes.
- A virtual circuit may reference physical circuits but cannot replace their protective-device or
  cable documentation.
- Validation and UI language must prevent virtual groupings from being mistaken for certified
  electrical topology.

### Kabel

- A cable has a stable UUID and may reference an Asset Engine asset when it is managed as inventory.
- It records an optional designation, cable type, conductor count, conductor cross-section, length,
  installation notes, source endpoint, target endpoint, and associated circuit when known.
- Endpoints may be distributions, rooms, junction points, devices, or documented external boundaries.
- Cable data is descriptive; no automatic voltage-drop, short-circuit, selectivity, or compliance
  calculation is part of this sprint.
- Archived or replaced cables keep both endpoints and circuit history.

### Beziehungen

The module uses allow-listed relationship types with service validation. Planned semantics include:

- `located_in`
- `feeds`
- `protected_by`
- `downstream_of`
- `connected_to`
- `uses_cable`
- `part_of_circuit`
- `maps_to_virtual_circuit`
- `replaced_by` through the Asset Engine workflow

Relationships with historical meaning are immutable after replacement. New active relationships to
soft-deleted records are rejected, while historical reads retain them.

### Fotos und Dokumente

- Buildings, rooms, distributions, protective devices, circuits, cables, and devices may have photo
  and document references.
- Media records store metadata, ownership, captions, timestamps, and provider-neutral references;
  binary data must not be embedded in ordinary API responses.
- Photos support installation overview, cabinet layout, labels, and component evidence.
- Documents support circuit schedules, diagrams, inspection records, datasheets, and manuals.
- Optional Immich or Nextcloud providers are accessed only through backend connectors and only when
  configured. Local electrical documentation remains usable without them.
- Secrets, provider credentials, and private provider URLs are never included in electrical read
  models or logs.

### Home Assistant Zuordnung

- An electrical device or circuit may store zero or more optional Home Assistant entity references.
- Associations use stable non-secret identifiers and an integration-account reference, not tokens or
  embedded credentials.
- The mapping is documentation/read-only. The module does not switch entities, change configuration,
  call services, or control external systems.
- Missing or unavailable Home Assistant must not block any local electrical workflow.

### Ersatzgeräte und Archivierung

- Replacing a device creates a new Asset Engine asset with a new UUID and JARVIS code.
- The former device is retired and connected through immutable replacement history; its electrical
  relationships, media, documents, and prior circuit assignment remain readable.
- The user explicitly decides which active circuit associations are copied to the replacement.
- Buildings, rooms, distributions, protective devices, circuits, and cables use soft delete or an
  explicit archive state where historical topology requires it.
- Archival never overwrites old technical data and never reuses stable identifiers.

## Backend

The future implementation must follow router -> service -> repository -> SQLModel boundaries and
dependency injection from `docs/DEVELOPMENT_GUIDELINES.md`.

Planned domain resources:

- `Building`
- `Room`
- `DistributionBoard`
- `ProtectiveDevice` with typed classifications for fuse, FI/RCD, LS, combined protection, and
  surge protection
- `Circuit`
- `VirtualCircuit` or an explicit circuit-kind discriminator
- `Cable`
- `ElectricalRelationship`
- `MediaReference`
- `HomeAssistantAssociation`

Generic devices remain `Asset` records and are referenced by UUID.

All APIs are planned below `/api/v1/electrical`, with CRUD, pagination, search, allow-listed sorting,
filters, detail reads, and archive behavior appropriate to each resource. Exact endpoint and schema
names must be finalized before this sprint changes from Draft to Approved.

Services must validate building ownership, room placement, distribution hierarchy, slot conflicts,
protective-device compatibility, product/asset references, circuit source/protection, cable
endpoints, virtual/physical distinctions, relationship cycles, soft-deleted references, and
replacement history. Multi-record creation, replacement, and archive operations are transactional.

## Frontend

The planned frontend includes:

- An electrical overview by building.
- Building and room navigation that works on desktop and mobile.
- Distribution-board list and detail views with rows/slots, installed protection, incoming supply,
  outgoing circuits, photos, and documents.
- Editors and detail views for protective devices, circuits, virtual circuits, and cables.
- Device assignment using existing Asset Engine assets and JARVIS codes.
- Search, filters, sorting, pagination, loading, empty, validation, conflict, and historical states.
- Readable visualization of supply/protection relationships without implying an engineering diagram
  or certification.
- Photo and document reference management.
- Optional read-only Home Assistant association fields.
- Explicit replacement and archive workflows with warnings about retained history.
- Responsive Vuetify layouts and full support for the persisted dark-mode default.

The frontend communicates only with `/api/v1`; it never accesses SQLite, Home Assistant, Immich, or
Nextcloud directly.

## Migrationen

No migration is created by this planning document.

The future implementation requires new additive Alembic revisions. Before approval, the sprint must
define final tables, columns, foreign keys, indexes, uniqueness rules, and backfills. Migrations must:

- Preserve every existing UUID, JARVIS code, asset, relationship, setting, and user value.
- Reference Asset Engine rows instead of copying them.
- Add constraints only after handling valid historical data.
- Work on both an empty database and a database at the previous revision.
- Include direct foreign-key and uniqueness tests with SQLite enforcement active.
- Never modify an already merged migration.

## Tests

The future implementation must include at least:

- Repository and service tests for every electrical resource.
- API CRUD, pagination, search, sorting, filter, and archive tests.
- Building/room ownership and distribution-hierarchy tests.
- Cycle and slot-conflict tests.
- Protection-chain tests for fuse, FI/RCD, LS, combined protection, and surge protection.
- Physical versus virtual circuit validation tests.
- Cable endpoint and circuit-association tests.
- Asset/device reference, replacement, and historical-read tests.
- Soft-deleted reference tests that reject new assignments but preserve old topology.
- Photo/document metadata tests without external providers.
- Home Assistant association tests proving read-only and offline behavior.
- Migration tests from the prior revision with existing Asset Engine data.
- Direct SQLite foreign-key and uniqueness tests.
- Frontend Vitest coverage for API contracts and critical editors/workflows.
- Ruff, mypy, pytest, Alembic, Vitest, vue-tsc, Vite, and Docker CI checks.

## Definition of Done

Sprint 0003 is complete only when:

- [ ] All planned electrical resources and approved `/api/v1/electrical` contracts are implemented.
- [ ] Buildings, rooms, distributions, every required protection category, devices, circuits,
      virtual circuits, cables, and relationships are usable end to end.
- [ ] Photos, documents, and optional read-only Home Assistant associations are supported without
      making integrations mandatory.
- [ ] Replacement and archival preserve UUIDs, JARVIS codes, topology, media, and history.
- [ ] Physical and virtual circuits are visibly and technically distinct.
- [ ] All writes use services and repositories with transaction boundaries and dependency injection.
- [ ] Migrations are additive, update-safe, and verified with pre-existing Asset Engine data.
- [ ] Desktop/mobile views, loading/error/empty states, and dark mode are complete.
- [ ] Required backend, frontend, database, migration, and regression tests pass.
- [ ] README, CHANGELOG, ADRs, API documentation, and this sprint status are updated.
- [ ] Full CI including Docker build is green.

## Abnahmekriterien

1. A user can create a building and rooms, place a distribution in a room, and navigate the complete
   hierarchy after a container restart without internet access.
2. A user can document fuses, FI/RCDs, LS devices, combined protection where applicable, and surge
   protection in a distribution with positions and optional technical values.
3. A user can create a physical circuit, assign its protection chain, cable, and existing Asset
   Engine devices, then trace the relationship from device back to source distribution.
4. A user can create a clearly marked virtual circuit and associate devices or physical circuits
   without creating a false physical cable/protection path.
5. A user can attach photo and document metadata while the module remains functional with Immich and
   Nextcloud disabled.
6. A user can associate Home Assistant entity identifiers without exposing credentials or enabling
   control actions; unavailable Home Assistant does not degrade local CRUD.
7. Replacing a device creates a new UUID/code, retires the old device, preserves the old topology and
   media, and records immutable replacement history.
8. Archiving any supported electrical record hides it from normal active lists, rejects new active
   references, and keeps historical detail reads intact.
9. Invalid cycles, cross-building assignments, conflicting positions, missing/deleted references,
   and inconsistent physical topology are rejected transactionally with understandable errors.
10. Upgrade tests demonstrate that existing settings, Asset Engine UUIDs, codes, relationships, and
    user data are unchanged after the electrical migrations.
11. Responsive frontend workflows and all required CI jobs, including Docker build, pass.

## Nicht Bestandteil

- No application, database, migration, or frontend code is part of this planning-only change.
- Switching, controlling, commissioning, or reconfiguring Home Assistant or electrical equipment.
- Electrical design approval, certification, inspection sign-off, or regulatory compliance claims.
- Automatic cable sizing, voltage-drop, fault-current, selectivity, load-flow, or protection
  calculations.
- Live metering, energy analytics, tariffs, forecasts, alerts, or automation rules.
- Automatic topology discovery from Home Assistant or another external service.
- User management, authentication, authorization, or public-internet exposure.
- Provider-specific credential storage beyond the existing integration settings foundation.
- Binary media storage inside ordinary database rows or API responses.
