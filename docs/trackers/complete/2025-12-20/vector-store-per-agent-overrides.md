<!-- SECTION: Metadata -->
# Milestone: Per-Agent Vector Store Overrides

_Last updated: 2025-12-20_  
**Status:** Completed  
**Owner:** @platform-foundations  
**Domain:** Cross-cutting  
**ID / Links:** [Vector store overrides design], [Containers override pattern], [Agent tooling flags], [Web app plan]

---

<!-- SECTION: Objective -->
## Objective

Enable per-agent vector store overrides (mirroring container overrides) so the frontend can safely gate file_search usage per agent and requests can target specific vector stores without global overrides, while keeping the implementation DRY and aligned with existing clean architecture patterns across backend and web app.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Chat + workflow request schemas support `vector_store_overrides` keyed by agent
- Overrides validate agent capability (`file_search`) and tenant ownership
- Overrides resolve to OpenAI vector store IDs without duplicating resolution logic
- Interaction context uses overrides before binding/spec/default resolution
- Web app threads vector store overrides through workflow run requests/streams
- Workflow nodes show vector store selectors only for file_search-capable agents
- Unit tests cover valid/invalid override paths
- `hatch run lint` and `hatch run typecheck` pass
- `pnpm lint` and `pnpm type-check` pass
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add a per-agent override request field for chat and workflow runs
- Resolver to validate and resolve override inputs (DB UUID or OpenAI vector store ID)
- Integrate overrides into interaction context resolution
- Unit tests for new behavior
- Web app workflow override wiring + UI gating for file_search
- Web app tests for tooling + override flow

### Out of Scope
- Changes to vector store CRUD endpoints
- Migration or data backfills

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Reuse container override pattern + existing vector store resolver |
| Implementation | ✅ | Backend + web app wiring complete |
| Tests & QA | ✅ | Backend + web lint/type-check + unit tests green |
| Docs & runbooks | ✅ | Tracker updated with completion notes |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Request field: `vector_store_overrides: { [agent_key]: { vector_store_id? | vector_store_ids? } }`.
- Resolver mirrors `ContainerOverrideResolver` but reuses `resolve_vector_store_ids_for_agent` to avoid logic duplication.
- InteractionContextBuilder applies per-agent overrides before binding/spec/default resolution.
- Keeps overrides in `services/agents/*` to avoid API layer coupling.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – API Schema

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add vector store override schema model | @platform-foundations | ✅ |
| A2 | API | Wire `vector_store_overrides` into chat + workflow requests | @platform-foundations | ✅ |

### Workstream B – Services

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Services | Add VectorStoreOverrideResolver | @platform-foundations | ✅ |
| B2 | Services | Integrate overrides into InteractionContextBuilder | @platform-foundations | ✅ |

### Workstream C – Tests & QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Tests | Unit tests for overrides + validation | @platform-foundations | ✅ |
| C2 | QA | Lint + typecheck | @platform-foundations | ✅ |

### Workstream D – Web App

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Web | Thread vector_store_overrides through workflow run + stream | @platform-foundations | ✅ |
| D2 | Web | Add file_search gating + vector store selector UI in workflow nodes | @platform-foundations | ✅ |
| D3 | Web | Web app tests + lint/type-check | @platform-foundations | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Confirm request shape + resolver pattern | Tracker created + plan agreed | ✅ | 2025-12-20 |
| P1 – Schemas | API request models updated | Schema compiles + lint/typecheck | ✅ | 2025-12-20 |
| P2 – Services | Resolver + context integration | Unit tests pass + lint/typecheck | ✅ | 2025-12-20 |
| P3 – Tests & QA | Coverage and cleanup | All backend checks green | ✅ | 2025-12-20 |
| P4 – Web App | Workflow UI + wiring | Web checks green + tests updated | ✅ | 2025-12-20 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Existing vector store service + resolution logic
- Container override pattern for reference

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Override ambiguity (single vs list) | Med | Enforce validation in schema + resolver |
| Override bypasses binding expectations | Med | Resolver validates agent capability + tenant ownership |
| Tooling mismatch on agents without file_search | Low | Resolver raises validation error early |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- Unit tests for new overrides in `tests/unit/agents/service` (pytest via hatch)
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- Web app unit tests for tooling (vitest)

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations.
- Requires OpenAPI export + frontend client regen in follow-up when UI work begins.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-20 — Added vector_store_overrides schema + request fields; lint/typecheck clean.
- 2025-12-20 — Implemented per-agent override resolver + workflow wiring; lint/typecheck clean.
- 2025-12-20 — Added override tests; lint/typecheck + targeted pytest clean.
- 2025-12-20 — Web app wiring + UI gating for file_search vector store overrides; `pnpm lint`, `pnpm type-check`, `pnpm test:unit` green.
