# Sprint 0012: docofhome visible branding

- Status: Approved
- Target branch: `feature/docofhome-branding`
- Depends on: Sprint 0011 and ADR-0010

> This document is the complete implementation contract for this sprint. The binding rules in
> `docs/DEVELOPMENT_GUIDELINES.md` apply in addition.

## Goal

The visible product identity changes from Tectoryn to **docofhome** without risking existing
installations, persisted data, API clients, Docker deployments, already allocated Asset codes, or
migration history. A single frontend metadata module becomes the source of truth for the product
name, slogan, and support label.

## Context

The project began with the working name JARVIS and later used Tectoryn as visible branding. The
repository, environment variables, SQLite path, theme identifiers, field names such as
`jarvis_code`, and existing Asset codes still contain legacy identifiers. Renaming those technical
contracts in the same change would create avoidable update and data-migration risk. The product
owner has selected `docofhome` as the final visible name; technical identifiers remain compatible
until a dedicated migration sprint can prove an automatic, reversible upgrade path.

## Requirements

- Browser title, application shell, default installation fallback, slogan, footer, README, current
  user-facing documentation, and new integration copy use `docofhome`.
- The brand is written in lowercase exactly as `docofhome`.
- Frontend product name, slogan, and support label are defined in one typed metadata module.
- Existing user-selected installation names remain unchanged and continue to take precedence in the
  application header.
- Existing APIs, routes, database tables, migrations, UUIDs, stored settings, secrets, Asset codes,
  backup archives, Docker mounts, and update behavior remain unchanged.
- Technical legacy identifiers including `jarvis_code`, `JARVIS_` environment variables,
  `jarvis.sqlite3`, theme IDs, repository name, and already allocated code values are not renamed.
- Documentation distinguishes clearly between visible branding and technical compatibility names.
- The change introduces no network requests, telemetry, external assets, or runtime dependency.

## Backend

- No backend API or persistence contract changes are required.
- User-visible backend and connector messages touched by the active Immich sprint may use
  `docofhome`, while Python module names, API paths, database identifiers, and environment variable
  names remain stable.
- Health/version responses remain schema-compatible.

## Frontend

- Add `frontend/src/config/branding.ts` with typed constants for product name, slogan, and support
  label.
- `App.vue` uses the constants for fallback installation name and visible slogan.
- The browser title is `docofhome`.
- The support footer uses the shared support-label constant.
- Tests assert the shared value rather than duplicating a former brand literal.
- Existing layout, responsive behavior, dark/light themes, routes, and user configuration remain
  unchanged.

## Migration

None. This sprint must not change the database schema or rewrite persisted values.

## Tests

- Frontend tests verify the support link still opens safely in a new tab and renders the central
  docofhome label.
- Existing frontend tests, `vue-tsc`, and the production Vite build remain green.
- Existing backend tests, Ruff, mypy, pytest, Alembic upgrade/check, and Docker build remain green to
  prove compatibility.
- Repository review verifies that intentionally retained technical legacy names are documented and
  no unsafe broad search-and-replace was applied.

## Definition of Done

- [ ] Visible application shell and browser metadata use `docofhome`.
- [ ] Frontend brand metadata is centralized and tested.
- [ ] README, CHANGELOG, current ADR/sprint/architecture text, and support copy use `docofhome`.
- [ ] Existing installation names and all persisted technical identifiers remain unchanged.
- [ ] No database migration or runtime data rewrite is introduced.
- [ ] Frontend, backend, migration, and Docker quality gates are green.
- [ ] The pull request contains no credentials, private URLs, generated data, or unrelated features.

## Acceptance criteria

1. A fresh installation displays `docofhome · Know your home.` and the browser tab reads
   `docofhome`.
2. An existing configured installation still displays its own installation name while the product
   slogan and footer use `docofhome`.
3. Existing `jarvis_code` values, database files, backups, environment variables, API paths, and
   Docker volumes work without manual changes.
4. The support link still targets the existing Buy Me a Coffee URL with `noopener noreferrer`.
5. A repository review can identify every intentionally retained legacy identifier from the
   compatibility documentation.

## Out of scope

- Renaming the GitHub repository, Docker image, package names, Python modules, API paths, database
  file, tables, columns, Alembic history, theme IDs, or environment variables.
- Reallocating or rewriting existing Asset codes.
- Introducing aliases, redirects, or migration shims for technical identifiers.
- Any new functional module or external-integration capability.
