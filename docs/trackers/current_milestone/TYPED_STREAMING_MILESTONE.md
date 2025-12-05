<!-- SECTION: Metadata -->
# Milestone: Typed Streaming Surface (Web Search, Handoffs, Citations)

_Last updated: 2025-12-04_  
**Status:** Complete  
**Owner:** @tan (platform foundations)  
**Domain:** Cross-cutting (Backend + Frontend)  
**ID / Links:** [Docs](../current_milestone), [SDK logs](../../integrations/openai-agents-sdk/runner_api_events/tool_events.json)

---

<!-- SECTION: Objective -->
## Objective

Expose a strongly-typed streaming surface (tools + citations + handoffs) end-to-end so chat UI can render web search/tool activity and provenance confidently, while preserving raw Responses fidelity for audit/debug.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Backend `StreamingChatEvent` includes typed tool-call payloads (starting with web_search), annotations (url_citation), handoff info, and a raw passthrough field.
- Streaming proxy `/api/v1/chat/stream` forwards new fields; non-breaking to existing clients.
- Frontend chat stream adapter parses new fields into typed unions (tool events, citations, handoffs) with safe fallback to raw.
- Tests/fixtures cover web search call + citation + handoff parsing.
- `hatch run lint` + `hatch run typecheck` (api-service) pass; `pnpm lint` + `pnpm type-check` (web-app) pass.
- OpenAPI artifact regenerated; frontend SDK regenerated.
- Tracker updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Extend backend schemas and SSE proxy for tool/citation/handoff fields.
- Add typed unions & parser in `lib/chat`.
- Minimal fixtures from SDK log for tests.
- Regenerate OpenAPI + frontend SDK.

### Out of Scope
- Full UX for citations/tool cards (to be tackled next).
- Code Interpreter/image-gen UI.
- Persisted analytics or telemetry.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Plan agreed: typed union + raw passthrough, additive schema. |
| Implementation | ✅ | Backend stream bridge emits raw_event/tool_call/annotations (web_search, code_interpreter, file_search); download proxy added. |
| Tests & QA | ✅ | Backend lint/typecheck; frontend lint/type-check/unit; adapters cover web_search/code_interpreter/file_search + citations. |
| Docs & runbooks | ✅ | Tracker updated; SDK fixture referenced; OpenAPI + SDK regenerated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Additive Pydantic schema changes (no breaking removals). New fields: `tool_call`, `annotations`, `raw_event`, `handoff` (agent→new_agent).
- Preserve raw Responses event for audit; expose typed unions for UI.
- Frontend adapter maps tool events to `ToolState`, citations to `ChatMessage.citations`, handoffs to lifecycle tags; unknown kinds logged, not fatal.
- Workflows reuse the same streaming envelope as agents. Stage/parallel metadata rides in tags on run items and raw events, but `StreamingChatEvent` (tool_call, annotations, raw_event, is_terminal) is identical across workflow and agent streams, so the frontend adapter stays shared.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Backend schema & stream proxy

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Extend `StreamingChatEvent` Pydantic model with tool_call, annotations, handoff, raw_event | @tan | ✅ (merged) |
| A2 | API | Pass-through in `/api/v1/chat/stream` + server stream helper | @tan | ✅ |
| A3 | Tests | Add fixture based on SDK web_search log; unit test stream parser | @tan | ✅ |
| A4 | QA | `hatch run lint`, `hatch run typecheck` | @tan | ✅ (latest run green) |

### Workstream B – Frontend typing & adapter

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Types | Extend `lib/chat/types` with tool/citation/handoff unions | @tan | ✅ |
| B2 | Adapter | Parse new events in `chatStreamAdapter`; safe fallback to raw | @tan | ✅ (web_search + annotations parsing added) |
| B3 | Tests | Adapter fixtures from SDK log; vitest coverage | @tan | ✅ |
| B4 | QA | `pnpm lint`, `pnpm type-check` | @tan | ✅ (latest run green) |

### Workstream C – SDK regeneration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | OpenAPI | `starter_cli.app api export-openapi --enable-billing --enable-test-fixtures` | @tan | ✅ (artifact updated) |
| C2 | SDK | `pnpm generate:fixtures` in web-app | @tan | ✅ (client regenerated) |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Plan & milestone documented | Milestone committed | ✅ | 2025-12-04 |
| P1 – Impl | Backend schema + adapter + tests | DoD items except regen | ✅ | 2025-12-06 |
| P2 – Regen & QA | OpenAPI+SDK regen, all checks green | DoD complete | ✅ | 2025-12-07 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI Responses API event shapes (web_search, handoff).
- OPENAI_API_KEY present for web_search registration (runtime).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Event shape drift from OpenAI | Med | Keep `raw_event` passthrough; additive typing; log unknown. |
| Front/back mismatch during rollout | Med | Regenerate SDK in same PR; additive only. |
| Fixture brittleness | Low | Base fixtures on documented SDK log; keep raw + typed. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `cd apps/api-service && hatch run lint && hatch run typecheck && hatch run pytest`.
- Frontend: `cd apps/web-app && pnpm lint && pnpm type-check && pnpm test:unit` (adapter coverage).
- Manual smoke: stream chat via workspace; confirm no crashes with/without web_search enabled.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No flags; additive schema. Requires OpenAPI export + SDK regen post-merge.
- If web_search disabled (no API key), new fields stay null/empty.
- Rollback: revert schema + regen SDK; no data migrations.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-04 — Milestone created; scope & plan recorded.

---

<!-- SECTION: Metadata -->
# Milestone: File Search Tool & Vector Store Autowiring

_Last updated: 2025-12-04_  
**Status:** Planned  
**Owner:** @tan (platform foundations)  
**Domain:** Agents / Retrieval  
**ID / Links:** RAG tools — see `docs/integrations/openai-agents-sdk/tools/rag`

---

<!-- SECTION: Objective -->
## Objective

Make the OpenAI `file_search` tool turnkey: agents can opt in with zero config (auto primary vector store per tenant) while still allowing explicit bindings/overrides for advanced setups.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `FileSearchTool` registered in ToolRegistry; visible via `/api/v1/tools`.
- Agent runs that include `file_search` get `vector_store_ids` injected via run_config using per-tenant resolution (primary store fallback) and optional agent/request overrides.
- Auto-provision: first `file_search` use creates/ensures tenant primary vector store; feature can be disabled via setting.
- Agent specs support `tool_keys=("file_search",)` plus optional `tool_configs.file_search` (binding mode + max_num_results/filters/ranking_options pass-through).
- New admin binding path to map `agent_key` → `vector_store_id` per tenant (backed by existing `agent_vector_stores` table).
- Tests cover resolution order, auto-create, binding override, and run_config payload correctness; streaming schema remains additive.
- OpenAPI artifact + frontend SDK regenerated; docs updated.
- `hatch run lint` + `hatch run typecheck` (api-service) and targeted pytest suite green.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- ToolRegistry registration of `file_search` (OpenAI hosted).
- Run-config injection for vector_store_ids and optional tool params.
- Auto primary-store creation + per-agent binding resolution.
- Minimal admin API/handler to bind/unbind agent→vector store per tenant.
- Tests + docs + OpenAPI/SDK regen.

### Out of Scope
- Frontend UX for uploading/attaching files (already handled by vector store CRUD).
- Cross-provider retrieval abstraction; only OpenAI.
- Complex multi-store routing policies (future).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Backend tooling & run config
| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Tools | Register `FileSearchTool` in `app/utils/tools/registry.py`; expose metadata. | @tan | ☐ |
| A2 | Runtime | Inject `tool_resources.file_search.vector_store_ids` (and optional params) in OpenAI run_config when tool present. | @tan | ☐ |
| A3 | Auto-store | Use `ensure_primary_store` on first use per tenant; guard with setting `auto_create_vector_store_for_file_search`. | @tan | ☐ |

### Workstream B – Agent bindings & config surface
| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Specs | Allow `tool_keys=("file_search",)` and `tool_configs.file_search` (binding mode: primary/required/named:<name>; plus max_num_results/filters/ranking_options pass-through). | @tan | ☐ |
| B2 | Binding | Add service helper + small API handler to bind/unbind `agent_key` → `vector_store_id` per tenant using `agent_vector_stores` table. | @tan | ☐ |

### Workstream C – Tests, docs, regen
| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Tests | Unit tests: (a) tool registration list, (b) resolution order (request override → agent binding → primary auto-create), (c) run_config payload matches selected store ids, (d) auto-create disabled => 400. | @tan | ☐ |
| C2 | Docs | Update RAG/tool docs + tracker; note defaults/overrides and setting name. | @tan | ☐ |
| C3 | Regen | Export OpenAPI + regenerate frontend SDK after schema changes. | @tan | ☐ |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `cd apps/api-service && hatch run lint && hatch run typecheck && hatch run pytest tests/unit/services/vector_stores tests/unit/test_tools.py`.
- Targeted new tests for resolution and run_config payloads.
- Manual: enable `file_search` on an agent, start chat with/without pre-existing store; verify tool_call shows `file_search_call` and citations; confirm `/api/v1/tools` lists file_search.
- Post-change: Export OpenAPI + regenerate SDK; run `pnpm lint && pnpm type-check` in web-app.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Missing OPENAI_API_KEY or vector store quota → runtime error | High | Guarded registration; clear 400 when auto-create disabled or quota hit. |
| Multi-tenant leakage via wrong store id | High | Resolve store ids scoped by tenant; tests cover binding resolution; enforce tenant checks in service. |
| Run_config shape drift in OpenAI API | Med | Keep additive; include raw passthrough; small end-to-end smoke with live key before release. |

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-04 — Milestone drafted; awaiting implementation.
