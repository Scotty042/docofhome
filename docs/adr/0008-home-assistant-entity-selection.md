# ADR-0008: Local Home Assistant entity visibility selection

- Status: Accepted
- Date: 2026-07-21

## Context

Tectoryn reads a complete Home Assistant snapshot through the REST and authenticated WebSocket APIs.
Large installations can expose thousands of entities, while a household may need only a smaller
subset for daily documentation and asset linking. The integration must remain read-only, existing
clients must continue to see all entities after an update, and a user must be able to intentionally
select zero entities.

An empty selection table alone cannot distinguish "not configured, show everything" from
"configured, show nothing". Filtering the upstream REST state endpoint is also not available in the
current connector contract, and deleting selections for temporarily absent entities would turn an
external outage into local data loss.

## Decision

- Tectoryn stores a local selection mode with the values `all` and `selected`.
- Absence of a settings row means `all`, preserving the pre-sprint behavior on upgrade.
- A separate table stores unique Home Assistant entity IDs selected by the user.
- `selected` with an empty table is a valid, explicit zero-entity view.
- Selection replacement is atomic and independent of Home Assistant availability.
- Unknown or temporarily absent selected IDs remain stored until the user changes the selection.
- The connector still loads a complete external snapshot. Selection filters the local read model; it
  does not claim to reduce Home Assistant transfer volume.
- Devices are derived from visible entities in `selected` mode. Device selection is not a second
  persistent identity.
- Existing total summary counts remain stable. Additive fields expose visible and selected counts.
- An additive `selection_scope=all` query lets the management UI browse selection candidates while
  normal reads default to `visible`.
- Entity selection never creates, removes, or rewrites Home Assistant-to-asset links.

## Consequences

- Updated installations behave exactly as before until a user enables selected mode.
- Users can deliberately create an empty Smart Home view without losing the configured mode.
- The local database gains two small additive tables and a new migration.
- Large Home Assistant payloads are still loaded to build the complete candidate set and live state
  snapshot; this sprint improves usability, not connector bandwidth.
- Renamed or removed external entity IDs can remain selected but invisible. This preserves intent and
  requires an explicit user action to remove stale IDs.
- Future automatic rules can extend the selection domain without changing current stored entity IDs,
  but they require a separate sprint and ADR.
