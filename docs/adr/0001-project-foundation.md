# ADR-0001: Project foundation

- Status: Accepted
- Date: 2026-07-20

## Decision

JARVIS is a Docker-only, API-first, single-user digital home twin using FastAPI, Vue 3, Vuetify, SQLite, and persistent external storage.

## Consequences

- Configuration must be possible through the web interface wherever technically possible.
- Application images remain stateless and replaceable.
- User data and settings survive updates.
- Integrations are optional and failures must not prevent core operation.
