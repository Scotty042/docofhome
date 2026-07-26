# ADR-0010: docofhome branding with stable legacy identifiers

- Status: Accepted
- Date: 2026-07-21

## Context

The application has used JARVIS as its original technical working name and Tectoryn as an interim
visible product name. The final visible product name is `docofhome`. Several long-lived technical
contracts still contain the original name, including the GitHub repository, `jarvis_code`,
`JARVIS_` environment variables, the SQLite filename and data paths, theme IDs, migration history,
and already allocated human-readable Asset codes.

A broad rename would mix a user-interface change with database, deployment, backup, API, and update
migrations. Existing installations must continue to start with their current Compose files,
environment variables, data directory, database, backups, and stored Asset identities. The visible
name can change independently because it is presentation metadata rather than domain identity.

## Decision

- The visible product name is lowercase `docofhome`.
- User-facing shell metadata, browser title, slogan, support label, README, current product
  documentation, and new user-facing integration copy use `docofhome`.
- Frontend branding values are centralized in a typed metadata module instead of repeated literals.
- A configured installation name remains user data and takes precedence over the product fallback in
  the header.
- Existing technical identifiers remain unchanged until a dedicated migration sprint supplies
  aliases, compatibility tests, automatic migration, rollback behavior, and release instructions.
- Retained identifiers include at least `jarvis_code`, `JARVIS_` environment variables,
  `jarvis.sqlite3`, `/data` layout, API paths, theme IDs, repository name, package/module names,
  Alembic revisions, and existing Asset code values.
- Documentation calls the user-facing value a `docofhome code` while naming `jarvis_code` only when
  discussing the stable API/database field.
- No persisted installation name, code, path, setting, secret, UUID, relationship, or backup manifest
  is rewritten by the visible-branding sprint.

## Consequences

- Existing installations receive the new product identity without deployment or data changes.
- Source code temporarily contains both `docofhome` branding and documented legacy technical names.
  This is intentional and not an incomplete search-and-replace.
- External scripts and API clients using current environment variables, paths, or fields remain
  compatible.
- A future technical rename is possible but must be a separate migration project with a compatibility
  window; it is not required for the visible product launch.
- Repository and Docker image renaming can be evaluated independently after redirects, pull/update
  instructions, and image-tag continuity are defined.
