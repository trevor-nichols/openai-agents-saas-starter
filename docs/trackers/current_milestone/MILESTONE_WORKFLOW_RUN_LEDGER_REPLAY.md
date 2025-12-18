<!-- SECTION: Metadata -->
# Milestone: Workflow Run Ledger Replay (Run-Centric, Exact UI Playback)

_Last updated: 2025-12-18_  
**Status:** Completed  
**Owner:** (TBD)  
**Domain:** Cross-cutting (Backend + Web)  
**ID / Links:**
- Baseline ledger playback milestone (completed): `docs/trackers/current_milestone/MILESTONE_CONVERSATION_LEDGER_PLAYBACK.md`
- Public SSE contract (authoritative event model): `docs/contracts/public-sse-streaming/v1.md`
- Workflow run replay API contract: `docs/contracts/workflow-run-replay/v1.md`
- SSE contract milestone (completed): `docs/trackers/current_milestone/MILESTONE_SSE_STREAMING_CONTRACT.md`
- Web parity milestone (completed): `docs/trackers/current_milestone/MILESTONE_PUBLIC_SSE_V1_WEB_APP_PARITY.md`
- Workflow API (run stream): `apps/api-service/src/app/api/v1/workflows/router.py`
- Ledger replay API (conversation-scoped today): `apps/api-service/src/app/api/v1/conversations/ledger_router.py`
- Ledger persistence schema: `apps/api-service/src/app/infrastructure/persistence/conversations/ledger_models.py`

---

<!-- SECTION: Objective -->
## Objective

Enable users to open any historical workflow run and see the **exact same UI transcript** (messages, tool cards, reasoning summary parts, citations, refusals, attachments) they saw during the original live run—just like chat replay—without missing components or losing tool context.

This milestone makes “workflow run replay” a **first-class API surface** (run-centric), rather than requiring the client to stitch together conversation IDs and event sources.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- New run-centric replay APIs exist:
  - `GET /api/v1/workflows/runs/{run_id}/replay/events` (paged JSON of `PublicSseEvent`)
  - `GET /api/v1/workflows/runs/{run_id}/replay/stream` (SSE replay emitting `PublicSseEvent` frames)
- Replay returns only ledger frames for that run:
  - filters ledger rows by `workflow_run_id = run_id`
  - preserves original ordering and patch semantics (`event_id`, `output_index`, `item_id`, `tool_call_id`)
- Web app workflow history uses replay (ledger) as the canonical source for “what the user saw”, not step summaries.
- Attachments are durable in replay UX:
  - the replay payload must contain stable identifiers (`object_id`)
  - presigned URLs can be refreshed on demand (no “dead link” experience)
- Tests green:
  - `cd apps/api-service && hatch run lint && hatch run typecheck && hatch run test`
  - `cd apps/web-app && pnpm lint && pnpm type-check && pnpm test`
- Docs/trackers updated:
  - this milestone doc
  - a contract doc for workflow run replay (see Workstream A)

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend: run-centric read APIs that replay persisted `public_sse_v1` frames for a single workflow run.
- Backend: stable cursoring/pagination semantics scoped to a run’s ledger slice.
- Frontend: workflow history surfaces (run detail + transcript + final output) powered by replay frames.
- Attachments in replay:
  - render durable downloads from stored `object_id` (+ re-presign when necessary)
- Contract documentation for the replay endpoints (not a new event contract; we reuse `public_sse_v1`).

### Out of Scope
- Changing the `public_sse_v1` contract schema (should not be needed).
- Provider/raw debug playback to the browser (server traces remain authoritative).
- Workflow graph per-node embedded streaming/replay UI (can be a later milestone).
- Major workflow run persistence refactors (e.g., making `workflow_run_steps` a full transcript store).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Replay is ledger-based; API is run-centric; event model is `public_sse_v1`. |
| Implementation | ✅ | Run-centric replay endpoints shipped; web history is replay-driven. |
| Tests & QA | ✅ | Backend + web unit/contract tests cover run scoping + paging invariants. |
| Docs & runbooks | ✅ | Replay endpoint contract doc and workflow feature notes updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

### Key decisions (locked)
- **Canonical replay source:** `conversation_ledger_events` (persisted `public_sse_v1` frames).
  - We do not reconstruct replay from `workflow_run_steps`.
- **API surface is run-centric:** clients request replay by `workflow_run_id` only.
  - Server resolves the run, authorizes tenant/user access, and locates the linked conversation internally.
- **Reuse existing event contract:** replay returns the same `PublicSseEvent` frames used in live streaming (`schema="public_sse_v1"`).
- **Attachment durability:** replay must not rely on long-lived presigned URLs.
  - Prefer stable `object_id` identifiers and re-presign on demand.

### Proposed endpoint shapes (Option A)
- `GET /api/v1/workflows/runs/{run_id}/replay/events?limit=500&cursor=...`
  - Returns an ordered list of `PublicSseEvent` payloads and a `next_cursor`.
- `GET /api/v1/workflows/runs/{run_id}/replay/stream?cursor=...`
  - Streams the same payloads as `data: <PublicSseEvent JSON>\n\n`.

### Cursor semantics (to document and test)
- Cursor must be stable and scoped to the run’s ledger slice.
- Ordering must match the original persisted stream ordering (`stream_id`, `event_id`, and insertion order constraints).
- The API must not leak events from other runs in the same conversation.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A — Contract + Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Docs | Add `docs/contracts/workflow-run-replay/v1.md` describing endpoints, cursor semantics, ordering invariants, auth rules, and attachment durability strategy (references `public_sse_v1`). | TBD | ✅ |
| A2 | Docs | Update workflow feature docs to point to replay as the canonical history surface (web + API notes). | TBD | ✅ |

### Workstream B — Backend APIs (Run-Centric Replay)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | API | Add run-centric router endpoints under workflows: `/workflows/runs/{run_id}/replay/events` and `/replay/stream`. | TBD | ✅ |
| B2 | Backend | Implement a ledger query method that filters by `(conversation_id, workflow_run_id)` while preserving deterministic ordering and pagination. | TBD | ✅ |
| B3 | Auth | Enforce tenant scoping + required scopes (`conversations:read`), ensuring users can only replay runs they are authorized to view. | TBD | ✅ |
| B4 | OpenAPI | Update schemas + regenerate OpenAPI artifacts; ensure web client types can be regenerated without manual edits. | TBD | ✅ |

### Workstream C — Frontend (Workflow History Powered by Replay)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | API | Add web-app API helper for run replay events (paged) + (optional) replay stream. | TBD | ✅ |
| C2 | UI | For a selected historical run, render transcript/tool UI from replay frames (same primitives as live stream) to guarantee “nothing disappears.” | TBD | ✅ |
| C3 | UI | Attachments: if replay frames contain attachments with `object_id` but missing/expired `url`, re-presign via storage endpoints (no dead links). | TBD | ✅ |
| C4 | UX | Ensure “Final” tab chooses run replay final payload as the primary source when available, with graceful fallback. | TBD | ✅ |

### Workstream D — Tests + Fixtures

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Backend | Add tests for replay scoping: same conversation with multiple runs must not cross-contaminate replay results. | TBD | ✅ |
| D2 | Backend | Add tests for cursor paging stability within a run slice. | TBD | ✅ |
| D3 | Web | Add unit tests ensuring workflow run replay renders expected tool cards/messages from a fixture. | TBD | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Lock API + contract doc outline | Milestone updated; endpoint shapes approved | ✅ | 2025-12-18 |
| P1 – Backend read path | Implement run-centric replay APIs | B1–B4 done; backend tests for scoping/paging green | ✅ | 2025-12-18 |
| P2 – Web integration | Wire workflow history to replay | C1–C4 done; web tests green | ✅ | 2025-12-18 |
| P3 – Hardening | Fixtures + docs polished | A1–A2 + D1–D3 done | ✅ | 2025-12-18 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Durable conversation ledger exists and is the canonical replay source: `docs/trackers/current_milestone/MILESTONE_CONVERSATION_LEDGER_PLAYBACK.md`
- `public_sse_v1` contract is authoritative and stable: `docs/contracts/public-sse-streaming/v1.md`

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Replay leaks events from other runs in same conversation | High | Enforce `(conversation_id, workflow_run_id)` filtering at query layer; add D1 tests. |
| Cursor paging produces duplicates/skips | Med | Define ordering + cursor semantics explicitly in contract doc; add D2 tests. |
| Attachment links expire and “history breaks” | High | Treat `object_id` as canonical; re-presign on demand; avoid persisting long-lived URLs as truth. |
| Replay requires both run_id and conversation_id | Low | Keep Option A contract: run-centric only; server resolves conversation internally. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend:
  - `cd apps/api-service && hatch run lint`
  - `cd apps/api-service && hatch run typecheck`
  - `cd apps/api-service && hatch run test`
- Frontend:
  - `cd apps/web-app && pnpm lint`
  - `cd apps/web-app && pnpm type-check`
  - `cd apps/web-app && pnpm test`
- Manual smoke:
  - Run a workflow with tools + attachments; confirm:
    - live stream shows tool cards
    - history replay shows identical tool cards
    - attachment downloads can be refreshed and do not disappear

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags (pre-release): ship as the default history behavior.
- No DB migrations expected (ledger already stores `workflow_run_id`), but new indexes may be added if query plan requires it.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-18 — Shipped run-centric workflow replay endpoints + web history powered by ledger replay; regenerated OpenAPI + web SDK; tests green.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-18 — Created milestone; selected Option A (run-centric replay endpoints).
