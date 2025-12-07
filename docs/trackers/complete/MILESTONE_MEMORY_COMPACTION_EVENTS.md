<!-- SECTION: Metadata -->
# Milestone: Memory Compaction Events

_Last updated: 2025-12-07_  
**Status:** In Progress  
**Owner:** @platform-foundations (assist: @assistant)  
**Domain:** Backend  
**ID / Links:** [Docs](../../integrations/openai-agents-sdk/memory/README.md), [Design notes](../../integrations/openai-agents-sdk/memory/long_term_memory_strategies/README.md)

---

<!-- SECTION: Objective -->
## Objective

Emit explicit, structured memory compaction telemetry that feels native to the OpenAI Responses API (start/stop-style events), reaches SSE chat/workflow streams, and is persisted in the run-event log—without affecting durable message history or existing client contracts.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- StrategySession emits a `memory_compaction` run item via lifecycle events when compacting.
- SSE streams (chat + workflows) forward the new event kind/run_item_type; clients can ignore safely.
- ConversationEvent persistence stores the event with payload metadata.
- Docs updated (provider README + streaming schema notes if needed).
- Tests cover stream emission, persistence, and backwards compatibility (clients ignoring).
- `hatch run lint` and `hatch run typecheck` pass.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Runtime hook for compaction events (StrategySession → LifecycleEventBus).
- Event normalization/streaming/persistence wiring.
- Minimal schema/documentation updates.
- Unit/contract tests.

### Out of Scope
- Token-based triggers or new memory strategies.
- Frontend rendering (will consume later once API is stable).
- Feature flags; shipped as default, backward-compatible.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Event shape decided (lifecycle `memory_compaction` + payload). |
| Implementation | ⏳ | Hooks wired in StrategySession/session manager; streaming/persistence in progress. |
| Tests & QA | ⏳ | Initial unit coverage added for compaction hook; streaming/persistence tests pending. |
| Docs & runbooks | ⏳ | To update after API contracts finalized. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add optional `on_compaction` callback to `StrategySession`; invoked when `_compact_items` replaces tool inputs/outputs.
- Service layer (`SessionManager`/`AgentService`) wires callback to emit `AgentStreamEvent` with `kind="response.memory.compacted"`, `run_item_type="memory_compaction"`, payload summarizing counts/ids/keep params, via `LifecycleEventBus` so it hits SSE and event log.
- `normalize_stream_event` passes the new kind/run_item_type through unchanged; downstream clients can ignore unknown kinds.
- Event log stores as `ConversationEvent` with `run_item_type=memory_compaction`, preserving ordering.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Runtime Emission

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Memory | Add `on_compaction` hook to `StrategySession` and invoke with metadata | @assistant | ✅ |
| A2 | Services | Wire hook to emit `AgentStreamEvent` via `LifecycleEventBus` | @assistant | ✅ |

### Workstream B – Streaming & Persistence

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | API | Ensure `normalize_stream_event` passes through new kind/run_item_type | @assistant | ✅ (reuse lifecycle kind) |
| B2 | Persistence | Project memory compaction events into `ConversationEvent` | @assistant | ✅ |

### Workstream C – Quality & Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Tests | Unit/contract tests for streaming + persistence + compatibility | @assistant | ✅ (hook + streaming/persistence) |
| C2 | Docs | Update provider/streaming docs with event semantics | @assistant | ✅ |
| C3 | QA | `hatch run lint` / `hatch run typecheck` | @assistant | ✅ |
| C4 | Targeted tests | chat/workflow compaction SSE contract tests | @assistant | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Design lock | Event shape + hook points agreed | README updated with plan | ✅ | 2025-12-07 |
| P1 – Impl & tests | Hooks, streaming, persistence, tests green | All workstreams A/B/C to ✅ | ⏳ | 2025-12-12 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI Agents SDK Responses API event model (no upstream change required).
- Existing LifecycleEventBus plumbing in AgentService/workflow runner.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Streaming clients break on new kind | Low | Keep schema backward-compatible; unknown kinds ignored; add docs. |
| Event storm on aggressive compaction | Med | Emit one event per compaction call; payload compact. |
| Ordering confusion with tool outputs | Low | Emit immediately after compaction within session mutation; preserve sequence. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `hatch run lint`
- `hatch run typecheck`
- Targeted unit tests: StrategySession compaction emits hook; chat/workflow stream includes `memory_compaction`; event log stores it.
- Optional manual SSE curl to verify payload shape.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No flags; ships default with backward-compatible payloads.
- No migrations required (existing `ConversationEvent.run_item_type` already free-form).
- Rollback: revert code; events remain harmless in log.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-07 — Milestone drafted; design approach recorded.
- 2025-12-07 — Implemented compaction hook in StrategySession; wired session manager/agent service emission & persistence; added initial unit test.
