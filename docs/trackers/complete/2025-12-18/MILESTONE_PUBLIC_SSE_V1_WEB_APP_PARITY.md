<!-- SECTION: Metadata -->
# Milestone: `public_sse_v1` Web App Parity (Chat + Workflows)

_Last updated: 2025-12-17_  
**Status:** Completed  
**Owner:** Web Platform (starter)  
**Domain:** Frontend  
**ID / Links:**
- Contract (authoritative): `docs/contracts/public-sse-streaming/v1.md`
- Provider/raw coverage (backend-centric): `docs/integrations/openai-responses-api/streaming-events/coverage-matrix.md`
- Web app capture matrix (chat vs workflows): `docs/trackers/evaluations/web-app/public-sse-streaming/00-public-sse-v1-capture-matrix.md`
- Key implementations:
  - Chat live stream capture: `apps/web-app/lib/chat/adapters/chatStream/consumeChatStream.ts`
  - Chat tool timeline (ledger replay): `apps/web-app/lib/chat/mappers/ledgerReplayMappers.ts`
  - Workflow stream capture hook: `apps/web-app/features/workflows/hooks/useWorkflowRunStream.ts`
  - Workflow live transcript builder: `apps/web-app/lib/workflows/liveStreamTranscript.ts`
  - Workflow debug log: `apps/web-app/features/workflows/components/runs/streaming/WorkflowStreamLog.tsx`

---

<!-- SECTION: Objective -->
## Objective

Deliver a clean, DRY, contract-first streaming implementation where **workflow streaming captures and surfaces everything chat does**, plus workflow-specific context, using a shared `public_sse_v1` projection layer.

The end state should be understandable and maintainable by a senior engineer: one public contract, one shared event-to-viewmodel projection, consistent behavior across live streaming and ledger replay.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Chat and workflow streams consume the same `public_sse_v1` projection primitives (no duplicated tool/citation/reasoning logic).
- Workflows are a superset: all `public_sse_v1` kinds captured by chat are also captured for workflow runs, plus workflow context grouping (stage/step/branch).
- Chat includes a **Debug events** panel using the same component model as workflows.
- Reasoning UI is chunk/part based (Activity-style bullets) driven by `reasoning_summary.part.*` + `reasoning_summary.delta`.
- Tests cover the shared projection layer and parity-critical behaviors (tool approvals, agent updates, citations, reasoning parts).
- Quality gates pass:
  - `just web-lint`
  - `just web-typecheck`
  - `just web-test`
  - `just backend-test` (contract fixtures should remain green)
  - Link checks (internal markdown link validation) are green
- Docs/trackers updated (capture matrix reflects new parity guarantees).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Create a shared, pure projection layer for `public_sse_v1` events under `apps/web-app/lib/streams/publicSseV1/`.
- Refactor:
  - Chat live streaming capture to support `agent.updated`, `tool.approval`, `reasoning_summary.part.*` and to stop inferring agent switches from `event.agent` diffs.
  - Workflow live transcript building to reuse shared projection, surfacing parity events.
  - Conversation ledger replay mappers to reuse the same projection code used by live streaming (avoid drift).
- Add a chat “Debug events” panel (same event rendering patterns as workflows).
- Upgrade reasoning display to part/chunk bullets (ChatGPT-style).

### Out of Scope
- Backwards compatibility shims (pre-release; contract-first refactor only).
- Provider/raw debug streaming to browsers (server traces remain authoritative for raw fidelity).
- New backend contract kinds or schema changes (unless required to fix a mismatch; those would be tracked separately).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Shared projection primitives live under `apps/web-app/lib/streams/publicSseV1/`; chat + workflows consume them. |
| Implementation | ✅ | Workflows are a superset of chat capture/surfacing; chat includes Debug events + reasoning parts UX. |
| Tests & QA | ✅ | Web lint/typecheck/unit tests green; parity-critical behaviors covered in unit tests. |
| Docs & runbooks | ✅ | Web app capture matrix updated; offline markdown link checks added and validated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

### Key decisions
- **Single projection layer**: introduce `public_sse_v1` accumulators/reducers that are pure and framework-agnostic.
- **No “pragmatic coupling”**: UI components do not branch on stream source (chat vs workflow) beyond workflow context rendering; event handling is shared.
- **Live + replay parity**: the same projection code is used for:
  - Live streaming (`parseSseStream` → events)
  - Persisted ledger replay (`/ledger/events` → events)
- **Debug events parity**: chat debug events use the same rendering model as workflow debug events.
- **Reasoning parts UX**: implement a chunk-based (bullet) UI driven by `reasoning_summary.part.added/done` and appended via `reasoning_summary.delta` per `summary_index`.

### Planned shared modules (web-app)
- `apps/web-app/lib/streams/publicSseV1/reasoningParts.ts` — state machine for parts + deltas.
- `apps/web-app/lib/streams/publicSseV1/citations.ts` — citation accumulation keyed by `item_id`.
- `apps/web-app/lib/streams/publicSseV1/tools.ts` — unified tool state (status/args/code/output/chunks + `tool.approval`).
- `apps/web-app/lib/streams/publicSseV1/transcript.ts` — transcript item ordering + in-place updates (`output_index`, `item_id`).
- `apps/web-app/lib/streams/publicSseV1/projector.ts` — orchestrates the above into reusable view models.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Shared `public_sse_v1` projection layer

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Lib | Define shared event helpers + invariants (`isTerminal`, envelope checks). | Web | ✅ |
| A2 | Lib | Implement reasoning parts accumulator (`reasoning_summary.part.*` + `reasoning_summary.delta`). | Web | ✅ |
| A3 | Lib | Implement unified tool accumulator (status/args/code/output/chunks + approvals). | Web | ✅ |
| A4 | Lib | Implement citations accumulator and transcript item ordering by `output_index`. | Web | ✅ |
| A5 | Tests | Add unit tests for projector edge cases and ordering invariants. | Web | ✅ |

### Workstream B – Chat parity + debug events

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Chat | Wire chat live stream to shared projector (drop duplicated tool/citation logic). | Web | ✅ |
| B2 | Chat | Surface `agent.updated` as the authoritative handoff signal. | Web | ✅ |
| B3 | Chat | Surface `tool.approval` in tool UI. | Web | ✅ |
| B4 | Chat | Add “Debug events” panel (shared component pattern with workflows). | Web | ✅ |
| B5 | Chat | Upgrade reasoning UI to part/chunk bullets. | Web | ✅ |

### Workstream C – Workflow parity (superset of chat)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | WF | Replace `buildWorkflowLiveTranscript` with shared projector output. | Web | ✅ |
| C2 | WF | Surface parity events in live transcript (memory checkpoints, agent updates, citations, tool approvals). | Web | ✅ |
| C3 | WF | Keep debug log as raw event viewer (but ensure kinds are fully represented). | Web | ✅ |

### Workstream D – QA, link checks, and docs sync

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Tools | Add internal markdown link checker (relative links + file existence). | Web | ✅ |
| D2 | Docs | Update capture matrix to reflect the new parity guarantees. | Web | ✅ |
| D3 | QA | Run `just web-lint`, `just web-typecheck`, `just web-test` after each phase; keep green. | Web | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Lock parity goals + UX decisions. | Milestone doc updated with decisions; scope agreed. | ✅ | 2025-12-17 |
| P1 – Shared projector core | Add shared projection modules + tests. | Chat/workflows can consume projector in isolation; unit tests green. | ✅ | 2025-12-17 |
| P2 – Chat integration | Refactor chat streaming + add chat debug panel + reasoning parts UI. | Chat captures/surfaces missing kinds; UI stable; tests green. | ✅ | 2025-12-17 |
| P3 – Workflow integration | Refactor workflow live transcript to shared projector. | Workflow live transcript is a superset of chat; debug log unchanged. | ✅ | 2025-12-17 |
| P4 – Docs + QA hardening | Matrix updates + link checks + regression tests. | Docs and link checks green; parity is enforced by tests. | ✅ | 2025-12-17 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Public contract must remain the authoritative source: `docs/contracts/public-sse-streaming/v1.md`.
- OpenAPI client types (`apps/web-app/lib/api/client/types.gen.ts`) must remain in sync with backend.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Projection drift across surfaces (chat vs workflows vs replay) | High | Centralize logic in shared projector and write parity-oriented unit tests. |
| O(n²) renders / poor performance due to rebuilding transcript per event | Med | Use accumulators that update in place; keep stable ordering by `output_index`. |
| UI complexity creep for reasoning parts | Med | Keep reasoning parts state machine minimal; render as list of parts, appended by `summary_index`. |
| Inconsistent “handoff/agent changed” semantics | Med | Treat `kind="agent.updated"` as authoritative; `event.agent` is context, not the routing signal. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Frontend:
  - `just web-lint`
  - `just web-typecheck`
  - `just web-test`
- Backend contract fixtures (regression safety):
  - `just backend-test` (especially streaming contract fixtures)
- Link checks:
  - Run internal markdown link checker (to be added in Workstream D1).
- Manual smoke:
  - Chat: run a stream with web search, image generation partials, MCP approval, and a handoff.
  - Workflows: run a workflow that produces tools + reasoning parts; confirm parity surfaces in live transcript + debug log.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags; ship contract-first refactor.
- No migrations required; frontend-only changes in this milestone (backend remains authoritative contract emitter).

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-17 — Created milestone; locked decisions:
  - Chat adds Debug events panel (shared component model with workflows).
  - Reasoning UI becomes part/chunk based (Activity-style bullets).
- 2025-12-17 — Implemented shared `public_sse_v1` projection primitives (tools, citations, reasoning parts) + offline markdown link checker.
- 2025-12-17 — Refactored chat + workflows to achieve capture/surfacing parity; updated capture matrix; web lint/typecheck/tests green.
