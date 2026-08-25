# Sprint NNNN: Title

- Status: Draft
- Target branch: `feature/short-description`
- Depends on: List required merged sprints or ADRs, or `None`

> This document is the complete implementation contract for this sprint. The binding standards in
> `docs/DEVELOPMENT_GUIDELINES.md` also apply.

## Ziel

Describe the concrete user or system outcome delivered by this sprint. The goal must be testable and
small enough for one coherent pull request.

## Hintergrund

Explain the problem, current state, relevant architecture, dependencies, and why the sprint is
needed now. Link required ADRs or earlier sprint definitions.

## Anforderungen

- List every functional requirement.
- State required workflows and error behavior.
- Define security, offline, responsive, and compatibility expectations.
- Identify stable identifiers and historical behavior where relevant.

## Backend

- Define domain models and ownership.
- Define versioned `/api/v1` endpoints and request/response behavior.
- Define repository and service responsibilities.
- Define validation, transaction, dependency-injection, pagination, search, sorting, filtering, and
  soft-delete behavior as applicable.
- State integration boundaries and failure behavior.

## Frontend

- Define pages, navigation, forms, lists, details, and workflows.
- Define desktop/mobile behavior and dark-mode expectations.
- Define loading, empty, validation, success, and error states.
- State which API contracts the UI consumes.

## Migrationen

- List every new table, column, index, constraint, or backfill.
- Explain how the migration remains additive and preserves existing UUIDs, settings, relationships,
  and user data.
- Define upgrade tests from the previous revision and fresh-database checks.
- Write `None` only when the sprint genuinely has no schema change.

## Tests

- Backend unit/service/repository/API tests:
- Direct database and constraint tests:
- Migration and update-safety tests:
- Frontend/Vitest tests:
- Regression and failure-path tests:
- Required static, build, and Docker checks:

## Definition of Done

- [ ] Every requirement in this sprint is implemented.
- [ ] No out-of-scope behavior was introduced.
- [ ] Backend and frontend contracts are typed and documented.
- [ ] Migrations are additive and update-safe.
- [ ] Required tests cover success, validation, failure, and historical behavior.
- [ ] Ruff, mypy, pytest, Alembic, Vitest, vue-tsc, Vite, and Docker checks are green.
- [ ] README, CHANGELOG, ADRs, and this sprint document are updated where relevant.
- [ ] The pull request contains no credentials, private URLs, generated data, or unrelated changes.
- [ ] Review findings are resolved and the acceptance criteria are demonstrated.

## Nicht Bestandteil

- List explicit exclusions.
- List deferred capabilities with a future sprint reference when known.
- State behaviors that must not be inferred or implemented in this sprint.
