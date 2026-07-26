# ADR-0003: Asset Engine domain and lifecycle

- Status: Accepted
- Date: 2026-07-20

## Context

All planned JARVIS modules need a shared representation of physical and logical inventory. The
foundation must support evolving classification, placement, tagging, and graph-like connections
without coupling feature modules directly to database access. Records must survive container
replacement and application updates, and ordinary deletion must not break historical references.

## Decision

- Model `Asset`, `Product`, `AssetType`, `Location`, `Label`, and `Relationship` as SQLModel tables.
  Use an explicit many-to-many link table for asset labels and directional source/target foreign
  keys for relationships.
- Give every domain record a UUID and created, updated, and deleted timestamps. A delete writes
  `deleted_at`; normal reads exclude deleted records while administrative reads may explicitly use
  `include_deleted=true`.
- Give every asset a separate human-readable JARVIS code. Asset types receive an immutable derived
  prefix, and an atomically incremented per-prefix database counter allocates unique sequence
  numbers. UUIDs remain the relational identity; codes are searchable external identifiers and are
  never accepted in asset write schemas.
- Store all tables in the same host-mounted SQLite database as application settings. Alembic owns
  schema evolution and migration `0004` creates only schema and indexes; it does not seed or replace
  user data.
- Keep HTTP routing, validation schemas, services, and repositories separate. Services own
  transactions and validate active references. Repositories own querying, allow-listed sorting,
  search, filters, pagination, label assignments, and soft-delete visibility.
- Make asset type mandatory for an asset. Product, location, labels, descriptive identifiers, and
  relationships remain optional so JARVIS is useful for progressively documented installations.
- Allow locations to form a hierarchy but reject missing parents and cycles. Reject relationships
  with missing/deleted endpoints or identical source and target assets.
- Require a product's optional asset type to match the asset type whenever that product is assigned.
  Product type changes are rejected if they would make an active asset inconsistent.
- Enable SQLite foreign-key enforcement through a connection listener for every application
  connection. Keep service validation for readable domain errors and to reject soft-deleted
  references; database constraints remain the final guard for direct writes.
- Normalize label names into a separately constrained key so case/whitespace variants cannot create
  accidental duplicates while preserving the user-visible spelling.
- Replace assets only through one transaction that retires the original, creates a new UUID and
  JARVIS code, and adds a typed `replaced_by` relationship. Once created, both the archived source
  asset and replacement relationship are immutable through normal CRUD operations.
- Expose the resource APIs only below `/api/v1`. Cap page size at 100 and use stable UUID
  tie-breaking so pagination remains deterministic.
- Build the Vue interface around assets while using product, type, location, label, and relationship
  endpoints as reference data. Keep the existing persisted theme behavior; dark mode remains the
  default.

## Consequences

- Future modules can reference stable asset UUIDs and share classification, placement, labels, and
  relationships without duplicating inventory models.
- Soft deletion preserves rows and relationship identifiers, but restoring or permanently purging
  records requires a future administrative workflow.
- Replacement history is explicit and queryable. A component refresh never reuses an existing UUID
  or JARVIS code, and failure at any point rolls back the new asset, relationship, status change, and
  counter allocation together.
- Referential integrity is enforced by both schema foreign keys and service validation. Writes
  through the supported API cannot point to missing or soft-deleted resources.
- The initial SQLite deployment is suitable for the intended single-user trusted network. The
  repository/service boundary keeps a later storage evolution possible without changing frontend
  contracts.
