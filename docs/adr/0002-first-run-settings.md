# ADR-0002: Persistent first-run settings

- Status: Accepted
- Date: 2026-07-20

## Context

JARVIS needs enough local configuration to identify an installation and render it consistently,
while remaining useful without external services. Container replacement and application updates
must not reset that configuration. Optional connector credentials must not be exposed through the
read API.

## Decision

- Store the singleton application configuration and one row per supported integration in SQLite
  under the externally mounted `/data` directory.
- Evolve both tables exclusively through Alembic migrations. Migrations create or transform schema
  and do not seed values over user-managed rows.
- Keep API routing below `/api/v1` and separate HTTP schemas, services, repositories, and SQLModel
  tables.
- Treat setup completion as one transaction and reject later attempts to complete first-run setup
  again. Normal edits use the dedicated settings endpoint.
- Make Home Assistant, Immich, and Nextcloud optional and independently enabled. JARVIS does not
  contact them during setup.
- Accept secrets only on writes. Read responses expose a `secret_configured` boolean; an omitted or
  empty secret during an edit preserves the stored value.
- Reject username/password userinfo in integration URLs. Store an optional non-secret `account`
  identifier separately; Nextcloud can pair that identifier with a write-only app password or
  token without placing credentials in the readable URL.
- Treat setup-status transport/database errors as unavailable state. Enter first-run setup only
  after a successful response confirms that setup is incomplete.
- Use dark mode as the initial theme while allowing a persisted light-mode preference.

## Consequences

- A fresh installation can be configured entirely in the browser without authentication or user
  management.
- The frontend can route deterministically to setup or the dashboard using persistent state.
- Container updates preserve settings as long as the host-mounted data directory is retained.
- Secrets remain locally stored in SQLite and are not returned to or logged by the application.
  The deployment therefore remains intended for a trusted private network as described in ADR-0001.
- Connector-specific requirements such as whether a Nextcloud account is mandatory are validated
  when that connector is implemented; the foundation keeps the field optional so skipped or
  token-only integrations remain representable.
