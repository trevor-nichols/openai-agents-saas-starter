<!-- SECTION: Metadata -->
# Milestone: Agent Tool Streaming (Public SSE v1)

_Last updated: 2025-12-25_  
**Status:** In Progress  
**Owner:** OpenAI Agents SaaS Starter Team  
**Domain:** Backend  
**ID / Links:** [PR TBD], [Contract docs: public-sse-streaming/v1.md]

---

<!-- SECTION: Objective -->
## Objective

Expose agent-as-tool streaming as first-class, scoped events in the public SSE contract so UI clients can render nested agent tool activity without compromising the primary stream semantics.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Public SSE schema includes scoped events and agent-tool tool status payloads
- Projector emits scoped events for agent tools without impacting root stream termination
- Agent tools stream nested events via SDK on_stream integration
- Contract docs and examples updated with agent-tool streaming
- Tests updated/added for agent-tool scope behavior
- `hatch run lint` and `hatch run typecheck` pass
- `apps/api-service/SNAPSHOT.md` updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add `scope` to public SSE events with `agent_tool` type
- Add `tool_type="agent"` to tool status payloads
- Bridge SDK agent tool stream events into SSE projector
- Golden NDJSON fixture + contract assertion updates

### Out of Scope
- UI rendering changes
- Backward compatibility shims or feature flags
- Workflow-specific scoping beyond agent tools

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Scope-based projection avoids duplication and preserves clean boundaries |
| Implementation | ⏳ | Pending | 
| Tests & QA | ⏳ | New fixture + assertions required |
| Docs & runbooks | ⏳ | Contract + example updates required |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce `scope` envelope in public SSE with `agent_tool` metadata.
- Add `tool_type="agent"` to the tool payload union.
- Use a scoped `ProjectionState` to isolate nested agent events from root stream state.
- Wire SDK `Agent.as_tool(on_stream=...)` to enqueue nested events into the stream pipeline.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract + Schema

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add `scope` + `AgentTool` payload to SSE schema | Team | ⏳ |
| A2 | Docs | Update v1 contract + new example fixture | Team | ⏳ |

### Workstream B – Streaming Implementation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Provider | Map SDK agent tool stream events | Team | ⏳ |
| B2 | Projector | Scoped ProjectionState + agent tool status | Team | ⏳ |

### Workstream C – Tests & QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Tests | Add agent-tool golden + assertion | Team | ⏳ |
| C2 | QA | Run lint/typecheck | Team | ⏳ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Milestone + design review | Tracker documented | ✅ |
| P1 – Schema | Schema + contract updates | Types compile | ⏳ |
| P2 – Impl | Projector + provider wiring | Tests pass | ⏳ |
| P3 – Docs/QA | Fixtures + snapshot + checks | All checks green | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI Agents SDK v0.6.4 `Agent.as_tool(on_stream=...)` support
- Existing public SSE contract tooling

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Nested events corrupt root stream state | High | Scoped ProjectionState + root-only terminal handling |
| Mislabeling agent tool events | Medium | Explicit `tool_type="agent"` + scope metadata |
| Tool stream ordering surprises | Low | Drain tool event bus at each stream iteration |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/contract/streams/test_stream_goldens.py`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags. Contract bump is additive and backward compatible for consumers that ignore `scope`.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-25 — Milestone initialized.
