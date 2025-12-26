<!-- SECTION: Metadata -->
# Milestone: Container Overrides + Run History (API)

_Last updated: 2025-12-20_  
**Status:** In Progress  
**Owner:** @platform-foundations  
**Domain:** Backend  
**ID / Links:** [Docs: Containers service], [Docs: Agent runtime context]

---

<!-- SECTION: Objective -->
## Objective

Enable per-agent container overrides for chat and workflow runs while persisting the container used in the run event log for audit/history. The outcome is a clean, tenant-safe override path that respects agent tool eligibility and leaves a reliable record of which container executed each run.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Chat and workflow request models accept `container_overrides` keyed by agent.
- Overrides are validated against agent capability (`code_interpreter`) and tenant scope.
- Runtime container selection uses precedence: request override → spec config → tenant binding → auto.
- Container context is persisted in conversation run events (and workflow run metadata).
- Tests cover validation, resolution precedence, and event persistence.
- `hatch run lint` and `hatch run typecheck` pass for the API service.
- Tracker updated with phase completion and changelog.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend request schemas for chat + workflows.
- Container override resolution service.
- Runtime context plumbing + tool resolver precedence.
- Run-event persistence for container context (audit trail).
- Workflow run metadata updates for container context.
- API service tests for overrides + run log persistence.

### Out of Scope
- Web app UI/UX for selecting containers.
- Non-Code-Interpreter tools or multi-tool container overrides.
- Backfilling historical runs.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Override contract + precedence defined. |
| Implementation | ✅ | P1–P3 request contracts + runtime + run history complete. |
| Tests & QA | ✅ | P1–P4 tests + lint/typecheck complete. |
| Docs & runbooks | ⏳ | Tracker only. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce `container_overrides: {agent_key: container_id}` on chat + workflow requests.
- Resolve overrides in a dedicated service to enforce tenant scope and tool eligibility.
- Extend `PromptRuntimeContext` to include resolved overrides for tool resolution.
- Persist container context as a run event with `tool_context` semantics for audit.
- Store per-run container context in workflow run metadata for quick retrieval.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Request Contracts

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add `container_overrides` to chat request schema. | @platform-foundations | ✅ |
| A2 | API | Add `container_overrides` to workflow run schema. | @platform-foundations | ✅ |

### Workstream B – Resolution + Runtime Integration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Service | Add container override resolution service. | @platform-foundations | ✅ |
| B2 | Runtime | Extend PromptRuntimeContext + tool resolver precedence. | @platform-foundations | ✅ |

### Workstream C – Run History Persistence

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Events | Persist container context as run event (chat + workflow). | @platform-foundations | ✅ |
| C2 | Workflows | Add container context to workflow run metadata. | @platform-foundations | ✅ |

### Workstream D – Tests + Hardening

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Tests | Validation + precedence unit tests. | @platform-foundations | ✅ |
| D2 | Tests | Run-event persistence tests. | @platform-foundations | ✅ |
| D3 | QA | Lint + typecheck green. | @platform-foundations | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Requirements + contract | Tracker updated + plan agreed | ✅ | 2025-12-20 |
| P1 – Contracts | Request schemas + validation | A1–A2 complete | ✅ | 2025-12-21 |
| P2 – Runtime | Resolver + tool precedence | B1–B2 complete | ✅ | 2025-12-22 |
| P3 – Audit | Run events + workflow metadata | C1–C2 complete | ✅ | 2025-12-23 |
| P4 – Hardening | Tests + lint/typecheck | D1–D3 complete | ✅ | 2025-12-24 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Container service configured (OpenAI API key, persistence).
- Agent specs must include `code_interpreter` for overrides to be valid.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Unauthorized container use | High | Resolve overrides via tenant-scoped DB lookups only. |
| Missing container bindings | Med | Clear 400 errors for invalid overrides; fallback to auto. |
| Audit gaps | Med | Persist container context in run events for every run. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test unit`
- Manual: chat run with override + verify run events show container context.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags; additive API fields.
- No data migrations expected (run events + workflow metadata only).
- Monitor for 400s indicating invalid overrides.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-20 — Milestone created; alignment captured for container overrides + run history.
- 2025-12-20 — P1 complete: request schemas updated + unit tests + lint/typecheck.
- 2025-12-20 — P2 complete: override resolver + runtime context + tool precedence + tests + lint/typecheck.
- 2025-12-20 — P3 complete: container context run events + workflow metadata + tests.
- 2025-12-20 — P4 complete: lint/typecheck/unit tests verified green.
