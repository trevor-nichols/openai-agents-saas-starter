<!-- SECTION: Metadata -->
# Milestone: Agent Tool Streaming (Public SSE v1)

_Last updated: 2025-12-25_  
**Status:** In Progress  
**Owner:** OpenAI Agents SaaS Starter Team  
**Domain:** Backend + Web  
**ID / Links:** [PR TBD], [Contract docs: public-sse-streaming/v1.md]

---

<!-- SECTION: Objective -->
## Objective

Expose agent-as-tool streaming as first-class, scoped events in the public SSE contract and render nested agent tool activity in the web UI without compromising the primary stream semantics.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Public SSE schema includes scoped events and agent-tool tool status payloads
- Projector emits scoped events for agent tools without impacting root stream termination
- Agent tools stream nested events via SDK on_stream integration
- Contract docs and examples updated with agent-tool streaming
- Tests updated/added for agent-tool scope behavior
- Web UI renders nested agent-tool streams under tool cards (chat + workflows)
- OpenAPI fixtures + HeyAPI client regenerated
- `hatch run lint` and `hatch run typecheck` pass (backend + web)
- `apps/api-service/SNAPSHOT.md` updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add `scope` to public SSE events with `agent_tool` type
- Add `tool_type="agent"` to tool status payloads
- Bridge SDK agent tool stream events into SSE projector
- Golden NDJSON fixture + contract assertion updates
- UI support for agent-tool scoped stream rendering (chat + workflows)
- Scoped stream accumulation utilities shared across chat + workflows

### Out of Scope
- Backward compatibility shims or feature flags
- Workflow-specific scoping beyond agent tools

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Scope-based projection avoids duplication and preserves clean boundaries |
| Implementation | ✅ | Backend streaming + scope handling complete |
| Tests & QA | ✅ | Fixtures + streaming tests green |
| Docs & runbooks | ✅ | Contract + example updates complete |
| Web UI | ✅ | Scoped streams rendered in chat + workflows |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce `scope` envelope in public SSE with `agent_tool` metadata.
- Add `tool_type="agent"` to the tool payload union.
- Use a scoped `ProjectionState` to isolate nested agent events from root stream state.
- Wire SDK `Agent.as_tool(on_stream=...)` to enqueue nested events into the stream pipeline.

---

<!-- SECTION: Professional Implementation Guidance -->
## Professional Implementation Guidance (SDK → Domain → Public SSE → UI)

**Goals:** maintain clean boundaries, avoid duplication, preserve SSE invariants, and keep the UI simple.

### 1) Provider boundary (OpenAI Agents SDK)
- The SDK is the *only* provider-specific layer. Everything above consumes provider-neutral `AgentStreamEvent`.
- Use `Agent.as_tool(on_stream=...)` to capture **nested** agent stream events into a small async bus.
- Map SDK events once via the shared mapper; **do not** fork scoped vs. root mapping logic.

### 2) Domain layer (provider-neutral)
- `AgentStreamEvent` owns the optional `scope` envelope; nested events never mutate root state.
- Root events remain the only ones allowed to trigger terminal `final|error`.

### 3) Public SSE projector
- Maintain a **separate ProjectionState per scope** to prevent nested events from corrupting root invariants.
- Project scoped events with the same envelope fields (`conversation_id`, `response_id`) as the root stream.
- Attach `scope` only; never re-route or special-case downstream consumers.

### 4) Web app
- Keep root tool accumulator and scoped tool-stream accumulator separate.
- Render scoped events under the parent tool card by `tool_call_id` with no backend bypasses or UI hacks.

### Design invariants
- **Single mapping path** for SDK → `AgentStreamEvent` (no scoped-only mapping).
- **Single contract** for public SSE; `scope` is additive and optional.
- **Scoped events never terminate** the root stream.

---

<!-- SECTION: Planned Professional Refinements -->
## Planned Professional Refinements (No UI Workarounds)

### R1 — Seed agent-tool status with agent name (no race on scoped events)
**Problem:** `tool.status` for agent tools can emit before scoped events arrive, leaving `tool.agent` blank.  
**Fix:** propagate a minimal, safe mapping of `{ tool_name → agent_name }` (or `{ tool_call_id → agent_name }` when available) from the provider metadata into the projector state so `tool.status` can be enriched immediately.

### R2 — Preserve nested tool typing in scoped streams
**Problem:** scoped mapping currently drops metadata, so nested tools inside agent-tools may be typed as generic functions and lose code-interpreter context.  
**Fix:** pass a minimal metadata bundle into the scoped mapper (e.g., `agent_tool_names`, `code_interpreter_mode`) so nested tool typing remains correct without leaking provider details.

### R3 — Keep invariants explicit in contract docs & tests
**Problem:** scoped behavior depends on ordering and terminal invariants.  
**Fix:** add/confirm contract assertions that scoped events:
1) never emit terminal events, and  
2) always include root `conversation_id`/`response_id`.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract + Schema

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add `scope` + `AgentTool` payload to SSE schema | Team | ✅ |
| A2 | Docs | Update v1 contract + new example fixture | Team | ✅ |

### Workstream B – Streaming Implementation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Provider | Map SDK agent tool stream events | Team | ✅ |
| B2 | Projector | Scoped ProjectionState + agent tool status | Team | ✅ |

### Workstream C – Tests & QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Tests | Add agent-tool golden + assertion | Team | ✅ |
| C2 | QA | Run lint/typecheck | Team | ✅ |

### Workstream D – Web UI

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | API | Regenerate OpenAPI fixtures + HeyAPI client | Team | ✅ |
| D2 | Streams | Add scoped agent-tool stream accumulator | Team | ✅ |
| D3 | Chat UI | Render nested agent-tool stream in tool accordion | Team | ✅ |
| D4 | Workflow UI | Render nested agent-tool stream in live + replay views | Team | ✅ |
| D5 | QA | Run `pnpm lint` + `pnpm type-check` | Team | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Milestone + design review | Tracker documented | ✅ |
| P1 – Schema | Schema + contract updates | Types compile | ✅ |
| P2 – Impl | Projector + provider wiring | Tests pass | ✅ |
| P3 – Docs/QA | Fixtures + snapshot + checks | All checks green | ✅ |
| P4 – Web UI | Scoped tool rendering | UI + tests pass | ✅ |

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
- `cd packages/starter_cli && python -m starter_cli.app api export-openapi --output apps/api-service/.artifacts/openapi-fixtures.json --enable-billing --enable-test-fixtures`
- `cd apps/web-app && OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures`
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags. Contract bump is additive and backward compatible for consumers that ignore `scope`.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-25 — Milestone initialized.
- 2025-12-25 — Added web UI workstream and scope.
- 2025-12-25 — Implemented web UI scoped agent-tool streams + regenerated client.
