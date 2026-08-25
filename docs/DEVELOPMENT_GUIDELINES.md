# JARVIS Development Guidelines

## Purpose and scope

This document defines the binding development standard for JARVIS. It applies to every feature,
fix, migration, integration, frontend change, and documentation change. A sprint document may make
requirements more specific, but it must not weaken these rules. Deviations require an explicit,
documented architecture decision before implementation.

## Architecture principles

JARVIS is an offline-first, API-first, Docker-first digital home twin. The architecture must remain
modular, testable, typed, and update-safe.

The required backend dependency direction is:

```text
API router -> service layer -> repository layer -> SQLModel / SQLite
```

- Dependencies point inward. Persistence and transport details must not leak into domain rules.
- A module owns its API schemas, services, repositories, models, migrations, and tests.
- Existing module boundaries and public contracts must be preserved.
- Shared behavior belongs in deliberately named shared components, not copied helper functions.
- Optional integrations must never be required for core JARVIS operation.
- External systems are never controlled unless a future sprint and ADR explicitly authorize it.

## Offline first

JARVIS must remain fully usable on the trusted local network without internet access or configured
integrations.

- Core data is stored locally in the persistent SQLite database.
- The frontend talks only to the local JARVIS API.
- A failed or unavailable integration must not prevent startup, navigation, or local CRUD flows.
- Features must not depend on external CDNs, hosted fonts, analytics, telemetry, or remote runtime
  assets.
- Network calls must be optional, bounded, observable, and isolated behind connector interfaces.
- Docker image replacement must not remove settings or user data from the external data volume.

## API contracts and versioning

- Every application API is exposed below `/api/v1`.
- Routers map HTTP requests and responses only. They may parse dependencies, call a service, and map
  known domain errors to HTTP status codes.
- Business rules, validation across records, transactions, generated identifiers, and integration
  behavior do not belong in routers.
- Request and response schemas are explicit and separate from persistence models where their
  responsibilities differ.
- Public response fields, accepted request shapes, endpoint semantics, and status codes are stable
  contracts.
- Breaking changes are forbidden. Extend contracts additively or introduce a new API version.
- Secrets, internal normalization fields, and persistence-only values must never enter read schemas.

## Backend layers

### SQLModel

- Persistent domain records use SQLModel table models.
- Models define database types, nullability, indexes, uniqueness, and foreign keys intentionally.
- Stable UUIDs are used for relational identity unless an ADR explicitly selects another strategy.
- Human-readable identifiers are separate from UUIDs and must not replace existing identities.
- Database constraints remain the final integrity guard even when services provide friendlier
  validation errors.

### Repository pattern

- Repositories own database reads and writes, query construction, pagination, search, sorting,
  filtering, and soft-delete visibility.
- Repositories receive a session through dependency injection; they do not create global sessions.
- Sort fields and filter fields are explicitly allow-listed.
- Repository methods do not encode HTTP concepts.

### Service layer

- Services own business rules, cross-record validation, transaction boundaries, generated values,
  replacement/archive workflows, and connector orchestration.
- A multi-record operation succeeds or fails as one transaction.
- Services call repositories instead of duplicating query logic.
- Domain failures use explicit exceptions that routers can translate consistently.

### Dependency injection

- Database sessions, repositories, services, settings adapters, and connectors are supplied through
  explicit constructors or FastAPI dependencies.
- Hidden mutable global state and service locators are forbidden.
- Dependencies must be replaceable in tests without network or production storage access.

## Persistence and migrations

### Alembic

- Alembic is the only mechanism for production schema evolution.
- A merged migration is immutable. Never edit an existing migration to change a deployed schema.
- Every schema change receives a new revision with the correct predecessor.
- Migrations are always additive and update-safe.
- Existing UUIDs, records, settings, relationships, and user-managed values must never be replaced,
  reset, or silently rewritten.
- Backfills must be deterministic, idempotent in intent, and tested against pre-existing data.
- New constraints must account for valid historical data before they become mandatory.
- Destructive drops, implicit data loss, and seed operations that overwrite user data are forbidden.
- Every migration must work from an empty database and from the previous released revision.

### Soft delete and history

- Domain records with historical relevance use soft delete, normally through `deleted_at`.
- Normal reads exclude deleted records unless the caller explicitly requests historical data.
- New active assignments to deleted references are rejected.
- Existing historical records remain readable with their prior references.
- Replacement creates a new record and an explicit immutable relationship; it never reuses or
  overwrites the old record's UUID or identifier.
- Physical deletion requires a separately approved retention or purge design.

## Configuration and secrets

- All application, user-facing, domain, and integration configuration is managed exclusively
  through the JARVIS web interface.
- A feature must not require users to edit source files, container images, or configuration files.
- Environment variables are limited to immutable deployment wiring, such as the persistent storage
  location or process logging; they are not an alternative application configuration surface.
- Credentials, access tokens, API keys, passwords, private URLs, and user-specific values must never
  be hardcoded or committed.
- Secrets are write-only through the API, redacted from responses, and excluded from logs.
- Example values must use clearly non-production placeholders such as reserved `.example` or
  `.test` domains.

## Frontend

- The frontend uses Vue 3, TypeScript, and Vuetify and communicates only through `/api/v1`.
- Screens must be responsive and usable on desktop and mobile.
- Dark mode remains the default; features must work in every supported persisted theme.
- Loading, empty, success, validation, unavailable, and failure states must be understandable.
- Frontend code must not duplicate backend business rules as an authority. Client-side validation
  improves feedback, while the backend remains authoritative.
- Configuration and optional integration settings must be editable in the web interface.

## Docker first

- The supported deployment target is Docker with persistent data outside the image.
- Development choices must work in the production image, not only in a local host environment.
- Dependencies are declared and pinned according to the repository's existing policy.
- Docker builds run in CI for every pull request.
- Application startup applies pending Alembic migrations before serving traffic.

## Language, typing, and comments

- Source code, identifiers, API field names, commit-facing technical terms, and code comments are in
  English.
- Documentation may be written in German or English, but each document should use one language
  consistently.
- Python code passes strict mypy checks. Type suppressions require a narrow, documented reason.
- TypeScript passes `vue-tsc --noEmit`; avoid unsafe casts and untyped transport data.
- Ruff is mandatory for Python code and tests.
- Comments are added only when they explain intent, constraints, safety, or non-obvious trade-offs.
  Comments that merely restate code are omitted.

## Tests and quality gates

Tests are mandatory for every behavior change and regression fix.

- Backend behavior is covered with pytest at the appropriate service, repository, API, migration,
  and direct-database levels.
- Frontend behavior and transport contracts are covered with Vitest.
- Foreign keys, uniqueness, transactional workflows, update migrations, secret redaction, and other
  persistence guarantees require tests that exercise the real database behavior.
- Bug fixes include a regression test that fails without the fix.
- Existing tests are never removed only to make a change pass.
- Tests do not depend on external services, private data, execution order, or container-only paths.

Before a pull request is considered complete, the relevant checks are green:

```text
ruff
mypy
pytest
alembic upgrade head
alembic check
vitest
vue-tsc
vite build
Docker build
```

## Development workflow

- Implementation work starts from a complete sprint definition in `docs/sprints/`.
- One feature branch contains one coherent sprint or narrowly scoped correction.
- Existing functions are not removed unless the sprint explicitly replaces them without breaking
  public behavior.
- README, CHANGELOG, relevant ADRs, and sprint status are updated with the implementation.
- Pull requests state what changed, why it changed, which migrations are involved, and which checks
  ran.
- Review findings are addressed with code, tests, and documentation before merge.
