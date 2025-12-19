<!-- SECTION: Metadata -->
# Milestone: Durable Conversation Ledger + Exact UI Playback (Tools + Memory Checkpoints)

_Last updated: 2025-12-17_  
**Status:** Completed  
**Owner:** (TBD)  
**Domain:** Cross-cutting (Backend + Web + Infra)  
**ID / Links:**
- Streaming ordering model (Responses API): `docs/integrations/openai-responses-api/streaming-events/00-intro.md`
- Public SSE contract milestone (baseline): `docs/trackers/current_milestone/MILESTONE_SSE_STREAMING_CONTRACT.md`
- Agents SDK SQLAlchemy session note: `docs/integrations/openai-agents-sdk/memory/sqlalchemy_session.md`
- API architecture snapshot: `apps/api-service/SNAPSHOT.md`
- Web architecture snapshot: `apps/web-app/SNAPSHOT.md`

---

<!-- SECTION: Objective -->
## Objective

Guarantee that conversation replays render **exactly the same transcript + tool components** a user saw during live streaming, across reloads and devices, while ensuring **memory compaction/summarization never mutates user-visible history**. Introduce explicit “memory checkpoint” breakpoints in the transcript so users can see when the model’s *context* was compacted without losing any visible content.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Durable, queryable, tenant-scoped **Conversation Ledger** persists an append-only log of **public_sse_v1** events (or an equivalent stable UI event model) sufficient to replay UI deterministically.
- Replay endpoint exists (non-streaming + streaming forms) to reconstruct the exact UI state from persisted events.
- Tool cards are stable on reload:
  - tool calls/outputs link by Responses API **`call_id`**
  - transcript ordering renders by **`output_index`** and patches by **`item_id`**
  - sequence ordering uses **`sequence_number`** for “activity” views when needed
- Memory strategies are decoupled from the ledger:
  - compaction/summarization affect only the model’s context view
  - a first-class `memory_checkpoint` ledger entry is appended at compaction points and rendered as a breakpoint in the UI
- Per-message deletion implemented:
  - user can delete only their **user** messages
  - deleting a user message removes that message and all subsequent content in that visible conversation line (messages + tool cards + checkpoints)
- Tests green:
  - backend unit/contract tests for replay determinism + tool linkage + deletion semantics
  - frontend unit tests for replay adapter + stable tool timeline reconstruction
  - `cd apps/api-service && hatch run lint && hatch run typecheck` pass
  - `cd apps/web-app && pnpm lint && pnpm type-check` pass
- Docs/trackers updated (this milestone + any dependent docs).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend: persistent ledger schema, write-path ingestion, replay read APIs, and deletion primitives.
- Frontend: a single replay path (persisted ledger) that yields identical rendering vs live stream.
- “Memory checkpoint” event type + UI rendering (breakpoint marker) for compaction/summarization.
- Strong invariants around ordering, anchoring, and tool linkage per Responses streaming model.

### Out of Scope
- Multi-branch “edit history” UX (explicit branch picker) unless required by deletion semantics.
- Long-term analytics/BI pipelines built from ledger data.
- Provider-specific raw payload storage exposure to browsers (public remains derived-only).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⏳ | Direction agreed: immutable user history + explicit memory checkpoints + deterministic replay by output_index/item_id. |
| Implementation | ⏳ | Existing systems persist messages + a partial run-event log; replay is not yet canonical/complete. |
| Tests & QA | ⏳ | Contract tests exist for public streaming, but replay determinism + deletion semantics need new coverage. |
| Docs & runbooks | ⏳ | This milestone doc to become the authoritative plan; follow-up design doc likely needed. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

### Locked principles
- **User-visible history is immutable**: memory compaction/summarization must never remove/replace past transcript content.
- **Replay is the product**: persisted data must be sufficient to reproduce the UI exactly as rendered during streaming.
- **Ordering/patch model (Responses API):**
  - render transcript by `output_index`
  - update items by `item_id` (and `content_index` for message parts)
  - treat `sequence_number` as stream application order / activity chronology
- **Tool linkage:** tool call ↔ tool output are joined by Responses API `call_id` (not item `id`).
- **Public data policy stays derived-only** for browsers; any richer raw provider payloads are optional server-only artifacts.

### Decisions (locked)
- **Persist every `public_sse_v1` frame** as the canonical source of truth for replay (no “final transcript JSON” as the authoritative store).
- **Large payloads:** store event JSON inline in Postgres up to **1 MiB per event**; overflow to blob storage via a pointer (still replayed as the same logical event), with tool anchoring by `call_id`.
  - Blob backend: **S3-compatible** via existing storage subsystem (**MinIO dev**, **S3 prod**).
- Payload encoding: **gzip**; integrity: **sha256**.
- **Replay API:** provide both
  - `GET /api/v1/conversations/{conversation_id}/ledger/events` (paged JSON) and
  - `GET /api/v1/conversations/{conversation_id}/ledger/stream` (SSE replay emitting the same `PublicSseEvent` frames).
- **Concurrency:** enforce one active run per conversation; **queue** subsequent user messages (FIFO) rather than interleaving.
  - Queue is **durable DB-backed**, max depth **10**.
  - “Stop generating” cancels the current run; the queue remains; next queued item runs automatically.
- **Deletion:** user deletion truncates the active conversation line; physical deletes happen via **background GC** (Postgres rows + blob artifacts) after truncation.
  - GC runs **hourly**; deletes truncated rows/blobs after **24h** retention.

### Proposed storage model (high-level)
- Introduce a `conversation_ledger_events` table (name TBD) keyed by:
  - `tenant_id`, `conversation_id`
  - `stream_id` (stable per streamed run / response)
  - `sequence_number` (monotonic apply order within a stream)
  - plus indexed fields used for replay: `item_id`, `output_index`, `kind`, `tool_call_id/call_id`, `response_id`
- Persist the **exact public_sse_v1 events** emitted to clients (post-redaction/truncation/chunking), so replay uses the same renderer/adapter as live streaming.
- Persist `memory_checkpoint` events as first-class ledger items with pointers to summary artifacts and compaction statistics.

### Read model
- Expose:
  - `GET /api/v1/conversations/{conversation_id}/ledger/events` (paged JSON) for fast reload
  - `GET /api/v1/conversations/{conversation_id}/ledger/stream` (SSE) for progressive hydration
- Keep existing `/messages` as a derived view (either projected from ledger or maintained as a fast summary table).

### Delete model (user message deletion)
- Implement “truncate from user message” semantics:
  - deleting a user message removes that message + all later visible items (including tool cards and memory checkpoints) from the active conversation line.
  - memory state for the conversation is reset to the truncation boundary.
- Implementation detail: represent truncation as an append-only “truncate” marker (tombstone boundary) plus **background GC** for storage cleanup.

### Defaults (locked)
- Spill threshold: **1 MiB** per event (inline) then blob.
- Blob backend: **S3-compatible** (MinIO dev, S3 prod), **gzip** + **sha256**.
- Replay: **paged JSON endpoint + SSE replay endpoint** (same `PublicSseEvent` frames).
- Queue: **durable DB-backed FIFO**, max depth **10**, “Stop generating” cancels current run (queue remains; next runs automatically).
- GC: runs **hourly**; deletes truncated rows/blobs after **24h** retention.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Design Spec (Replay + Ledger Invariants)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Design | Write a short design doc locking invariants: ordering, patch semantics, tool linkage by `call_id`, replay API shapes. | TBD | ✅ |
| A2 | Design | Define `memory_checkpoint` event schema + UI rendering requirements. | TBD | ✅ |
| A3 | Design | Decide deletion persistence model (hard-delete vs revision/branch tombstone) and required audit semantics. **Decision: tombstone boundary + background GC.** | TBD | ✅ |
| A4 | Design | Lock blob spill threshold + backend (S3/MinIO) + compression/hash strategy for large event payloads. | TBD | ✅ |
| A5 | Design | Specify run-queue semantics (FIFO, persistence, cancellation, max depth) and related UX/alerts. | TBD | ✅ |
| A6 | Design | Define background GC policy for truncated data (retention window, scheduling, operator controls). | TBD | ✅ |

### Workstream B – Persistence Schema (Postgres + migrations)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | DB | Add ledger table(s) + indexes for conversation replay and tool grouping. | TBD | ✅ |
| B2 | DB | Add storage for memory summaries + checkpoint metadata (if not already covered). (Covered by existing `conversation_summaries` + ledger payloads.) | TBD | ✅ |
| B3 | DB | Add deletion/truncation primitives (constraints, FK behavior, cascade strategy). | TBD | ✅ |
| B4 | DB | Add durable run queue storage (FIFO items per conversation). | TBD | ✅ |

### Workstream C – Backend Write Path (Capture what UI sees)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | API | Capture projected public_sse_v1 events during streaming and persist to ledger (exact bytes/JSON). | TBD | ✅ |
| C2 | Tools | Ensure stored tool linkage uses `call_id` consistently across tool.status/args/output events. | TBD | ✅ |
| C3 | Memory | On compaction/summarization, append `memory_checkpoint` ledger event (with stats + summary pointer). | TBD | ✅ |

### Workstream D – Backend Read Path (Replay APIs)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | API | Implement replay endpoints (paged) returning ordered ledger events for deterministic reconstruction. | TBD | ✅ |
| D2 | API | Implement optional replay streaming (SSE) for progressive hydration. | TBD | ✅ |
| D3 | Auth | Enforce tenant scoping + scopes (`conversations:read`) for replay endpoints. | TBD | ✅ |

### Workstream E – Frontend Replay (Single source of truth)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | UI | Build a replay adapter that consumes persisted public_sse_v1 events and reconstructs transcript + tool timeline exactly. | TBD | ✅ |
| E2 | UI | Ensure tool cards render stably on reload (output_index ordering + item_id patch + call_id joins). | TBD | ✅ |
| E3 | UI | Render `memory_checkpoint` breakpoint UI. | TBD | ✅ |

### Workstream F – Per-message Deletion (User truncation)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| F1 | API | Add endpoint to delete a user message and truncate subsequent content (authorization + validation). | TBD | ✅ |
| F2 | Backend | Reset memory state to truncation boundary and ensure future runs continue from the truncated view. | TBD | ✅ |
| F3 | UI | UI affordance + confirmation; rehydrate conversation from replay after deletion. | TBD | ✅ |

### Workstream G – Tests + QA + Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| G1 | Backend | Unit tests for ledger persistence + replay determinism; contract tests with golden replays. | TBD | ✅ |
| G2 | Frontend | Unit tests for replay adapter and deletion UX invariants. | TBD | ✅ |
| G3 | Docs | Document replay model, deletion semantics, and memory checkpoints; update trackers. | TBD | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Lock invariants + defaults | Decisions locked in this tracker | ✅ | 2025-12-17 |
| P1 – Storage | Ledger + checkpoint tables | B1–B3 completed | ✅ | 2025-12-17 |
| P2 – Capture | Persist public events + checkpoints | C1–C3 completed | ✅ | 2025-12-17 |
| P3 – Replay | Replay APIs + frontend adapter | D1–E3 completed | ✅ | 2025-12-17 |
| P4 – Deletion | Truncate semantics end-to-end | F1–F3 completed | ✅ | 2025-12-17 |
| P5 – QA/Docs | Tests + runbooks | G1–G3 completed | ✅ | 2025-12-17 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Baseline public streaming contract (`public_sse_v1`) complete: `docs/trackers/current_milestone/MILESTONE_SSE_STREAMING_CONTRACT.md`
- Postgres migrations + infra already present (Alembic).
- Existing attachment storage services (for large artifacts) available if chosen.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Ledger size growth (tools can output “anything”) | High | Store chunked events exactly as streamed; define retention/export strategy; optional external blob store for very large fields. |
| Replay drift if contract changes | Med | Persist the exact projected public events and version them (schema field already exists in contract). |
| Duplicate/missing tool linkage | High | Enforce `call_id` invariants at write time; add integration tests that replay tool calls/outputs across reload. |
| Deletion semantics conflict with append-only ledger | Med | Use an explicit truncation boundary (tombstone marker) + background GC; test it end-to-end. |
| Concurrency interleaves runs and breaks ordering | High | Enforce per-conversation run lock/lease and **queue** new user messages (FIFO); prevent interleaving. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend:
  - Unit tests for ledger write/read ordering invariants and `call_id` linkage.
  - Contract test: record a stream with tools, persist, replay, and assert identical UI-relevant state.
  - `cd apps/api-service && hatch run lint && hatch run typecheck && hatch run test`
  - Optional: `cd apps/api-service && just smoke-http` (runs the live HTTP smoke suite against a locally started api-service).
- Frontend:
  - Unit tests for replay adapter and tool timeline reconstruction.
  - Manual: create a chat with tool calls, reload the page, confirm tool cards + ordering are preserved.
  - `cd apps/web-app && pnpm lint && pnpm type-check && pnpm test`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Add migrations via `just migration-revision …` + `just migrate`.
- No feature flags intended (unreleased product); ship as the default persistence/replay path.
- Add retention settings (even if generous) and an operator export path before production launch.
- Ensure per-message deletion is audited and safe (tenant scoping, auth, and strong tests).
- Add/operate background GC for truncated ledger rows + associated blob artifacts.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-17 — Draft milestone created; design direction locked: immutable user history + exact replay + memory checkpoints.
- 2025-12-17 — Decisions locked: persist every `public_sse_v1` frame; blob spill strategy for large payloads; queue concurrency; background GC after truncation.
- 2025-12-17 — Defaults locked: 1 MiB spill threshold; S3/MinIO gzip+sha256; replay JSON+SSE; durable FIFO queue depth 10; hourly GC w/ 24h retention.
- 2025-12-17 — P1 complete: added Postgres schema + migration for conversation ledger segments/events + durable run queue storage.
- 2025-12-17 — P2 complete: persist every emitted `public_sse_v1` frame during streaming; add `memory.checkpoint` event + contract golden + unit coverage for ledger recorder spillover.
- 2025-12-17 — P3 complete: added ledger replay endpoints (paged JSON + SSE) and wired web-app replay adapter (tools + memory checkpoints) to persisted public_sse_v1 frames.
- 2025-12-17 — P4 complete: added per-message deletion (truncate-from-user-message) API + UI, reset memory state, and added test coverage.
