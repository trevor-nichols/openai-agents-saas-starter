<!-- SECTION: Metadata -->
# Milestone: Conversational Memory Strategies (API)

_Last updated: 2025-12-07_  
**Status:** In Progress  
**Owner:** @platform-foundations  
**Domain:** Backend  
**ID / Links:** This tracker; refs: `apps/api-service/SNAPSHOT.md`, `docs/integrations/openai-agents-sdk/memory/long_term_memory_strategies`

---

<!-- SECTION: Objective -->
## Objective

Enable configurable long-term memory strategies (trim, summarize, compact, memory injection) in the API service so agent runs can stay within context limits while keeping auditability and predictable behavior. Deliver a clean, extensible backend foundation that other surfaces (web/app/CLI) can call without embedding strategy logic in clients.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Strategy-aware session wrapper(s) built atop `SQLAlchemySession`, supporting trim, summarize, and compact behaviors, with defaults preserving current behavior.
- Per-request and per-conversation configuration plumbed through the chat APIs and SessionManager to the session store.
- Durable audit history (`agent_messages`, `agent_run_events`) remains lossless; strategy mutations affect only SDK session views.
- Optionally persisted summaries for cross-session memory injection with schema + service hook.
- Migrations (if any) applied; `hatch run lint` and `hatch run typecheck` pass; relevant tests added/updated and green.
- Tracker and docs updated; rollout notes captured.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend (API service) session-layer adaptations for memory strategies.
- Request/route-level plumbing to select strategies per conversation/request.
- Optional persisted summaries for cross-session injection (backend only).
- Tests, metrics, and observability for the new strategy paths.

### Out of Scope
- Frontend UI controls or UX for selecting strategies (will consume backend later).
- Vector-store/RAG changes; external memory stores beyond Postgres/Redis already present.
- Provider-specific behavior outside OpenAI Agents SDK session handling.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Strategy adapter + API plumbing design finalized. |
| Implementation | ✅ | StrategySession + layered defaults (request > conversation > agent) with API plumbing & persistence fields landed. |
| Tests & QA | ✅ | Unit coverage for strategy mapping + session behaviors; lint/typecheck green. |
| Docs & runbooks | ✅ | Backend memory doc updated; rollout notes pending minimal addition. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Wrap `agents.extensions.memory.SQLAlchemySession` with strategy-aware adapters (trim/summarize/compact) while delegating storage to existing SDK tables (`sdk_agent_sessions`, `sdk_agent_session_messages`).
- Extend SessionManager/SessionStore to accept a `MemoryStrategyConfig` (enum + knobs) and build the appropriate wrapped session per request/conversation.
- Keep durable audit history unchanged; compaction/summarization only touches SDK session view. Run-event projection continues to capture original tool calls/results before compaction.
- Optional cross-session memory injection: persist summaries in Postgres (new table) and inject into system instructions during context build.
- Configuration surface: per-request override plus per-conversation defaults stored alongside conversation metadata (requires small schema extension if used).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Session Strategy Adapters - ✅ COMPLETE

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Design | Finalize adapter API over `SQLAlchemySession` (strategy enum, config struct, lifecycle). | @platform-foundations | ✅ |
| A2 | Impl | Implement trim/summarize/compact wrappers with placeholder parity to docs; ensure async safety and no double writes. | @platform-foundations | ✅ |
| A3 | Tests | Unit tests against in-memory + Postgres session to verify turn triggers, placeholder shapes, and no data loss. | @platform-foundations | ✅ |

### Workstream B – API Plumbing & Config Persistence

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | API | Extend chat request schemas + SessionManager to accept optional `memory_strategy` payload; default = current behavior. | @platform-foundations | ✅ |
| B2 | Persistence | Schema addition for per-conversation defaults and summary storage; migrations + repository updates. | @platform-foundations | ✅ |
| B3 | Metrics/Logs | Add metrics for strategy activations and context-saved deltas; structured logs for debugging. | @platform-foundations | ✅ |
| B4 | Strategy resolution | Layered resolution: request > conversation > agent > none; agent defaults in specs/registry and source logging. | @platform-foundations | ✅ |

### Workstream C – Cross-Session Memory Injection (Optional slice)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Storage | Add summary persistence (table + repo/service) decoupled from audit history. | @platform-foundations | ✅ |
| C2 | Runtime | Inject summaries into system instructions when enabled; ensure freshness/tenant scoping. | @platform-foundations | ✅ |
| C3 | Tests | Contract/unit coverage for injection resolution and storage; targeted unit tests added. | @platform-foundations | ✅ |

### Workstream D – QA & Rollout

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Validation | `hatch run lint`, `hatch run typecheck`, targeted pytest suites (conversations, agents runtime). | @platform-foundations | ✅ |
| D2 | Docs | Update memory strategy docs and API reference; finalize rollout notes. | @platform-foundations | ✅ |
| D3 | Ops | Ensure migrations are idempotent; note feature flags/toggles (none planned). | @platform-foundations | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Design | Adapter/API design, schema decision, test plan | Design doc captured in tracker; no open questions blocking impl | ✅ | 2025-12-10 |
| P1 – Impl | Adapters + API plumbing + metrics | Tests green locally; migrations applied | ✅ | 2025-12-17 |
| P2 – QA/Docs | Regression + contract tests; docs/rollout | Lint/typecheck/tests green; docs updated; ready for PR | ✅ | 2025-12-19 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI Agents SDK version pinned in `pyproject.toml` (ensure strategy classes remain compatible).
- Existing `sdk_agent_sessions` tables present (migration `6724700351b6`); migrations may add summary/default fields if chosen.
- Tokenizer availability if we later add token-based triggers (optional).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Strategy mutates session items and could hide data from audit views | Med | Keep durable history writes unchanged; add tests asserting run_event capture before compaction. |
| Schema additions could block deploy if not migrated | Med | Gate features behind defaults; ensure Alembic migration shipped and backward compatible. |
| Summarization quality variance | Low | Make summary provider pluggable and optional; default to noop unless configured. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- Targeted pytest: `hatch run pytest tests/unit/conversations tests/unit/agents/runtime tests/unit/conversations/persistence/test_run_event_store.py`
- If migrations added: `hatch run pytest tests/integration/test_postgres_migrations.py` (with Postgres) and smoke chat path.
- Manual: run a streamed chat with compacting enabled; verify `agent_run_events` still contain original tool outputs, while SDK session shows placeholders.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Default behavior remains “no strategy”; enabling requires passing `memory_strategy` (request), setting conversation defaults, or agent defaults.
- New PATCH: `/api/v1/conversations/{id}/memory` (conversations:write, tenant ADMIN) to set/clear per-conversation defaults. Send `null` to clear a field and re-inherit agent defaults.
- Migrations: run `just migrate` (adds memory columns, summaries table, nullable flags). SQLite auto-create stays for tests only.
- No feature flags; rollout is controlled via defaults and API inputs.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-07 — Tracker created; design/impl work not started.
- 2025-12-07 — StrategySession (trim/summarize/compact) implemented with tests; lint/typecheck green.
- 2025-12-07 — Workstream B (API schema, session plumbing, migration, logging, layered defaults) completed; lint/typecheck + targeted tests green.
- 2025-12-07 — Workstream C (summary storage + injection + tests) completed; lint/typecheck + targeted tests green.
- 2025-12-07 — Conversation memory PATCH endpoint added; docs refreshed; lint/typecheck/tests green.
