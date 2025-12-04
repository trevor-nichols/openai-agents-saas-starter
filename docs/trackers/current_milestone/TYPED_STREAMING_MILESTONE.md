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
