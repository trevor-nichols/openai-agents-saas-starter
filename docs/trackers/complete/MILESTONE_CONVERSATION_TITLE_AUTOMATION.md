<!-- SECTION: Metadata -->
# Milestone: Conversation Title Automation

_Last updated: 2025-12-07_  
**Status:** In Progress  
**Owner:** @codex (Platform Foundations)  
**Domain:** Backend  
**ID / Links:** n/a

---

<!-- SECTION: Objective -->
## Objective

Automatically generate concise, user-facing titles for conversations on first message using an internal, non-public OpenAI invocation, persist them alongside conversations, and stream the title to clients via SSE so UIs can update in real time.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- New `display_name` (and timestamp) stored on `agent_conversations`; migration applied.
- Internal title generator uses `gpt-5-mini` with SSE-compatible flow; no new public endpoints or agent specs.
- Title emitted in chat SSE stream and returned on conversation list/search/history APIs.
- Backward compatibility: `topic_hint` remains; clients can fall back gracefully.
- Tests/lint/typecheck: `hatch run lint`, `hatch run typecheck` green (API service scope).
- Docs/trackers updated (this milestone, changelog entries as work lands).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Schema migration for conversation titles.
- Internal title generation service wired to first-user-message path.
- SSE emission of generated title on chat stream.
- API schema updates (summary/search/history) to expose `display_name`.
- Unit tests for title generation and SSE payload.

### Out of Scope
- UI changes in web-app (handled separately).
- Retroactive backfill for existing conversations (could be a later task).
- Multi-language titling or user-editable titles.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⏳ | Plan agreed (internal agent via SDK, SSE), need to finalize details while implementing. |
| Implementation | ⏳ | Not started; awaiting migration + service wiring. |
| Tests & QA | ⏳ | Will add unit coverage for service + SSE event. |
| Docs & runbooks | ⏳ | Milestone draft created; update changelog as work lands. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add `display_name` (varchar ~128) and `title_generated_at` to `agent_conversations`; surface via domain record and API schemas.
- Create `TitleService` under `app/services/conversations/` using direct OpenAI SDK call (`gpt-5-mini`, low temp, short token limit). No public agent spec.
- Trigger generation after first user message (non-blocking) and emit SSE lifecycle event carrying the title; fail-open if generation fails.
- Extend streaming DTOs to include optional `display_name` so clients can update live.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Schema & Domain

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | DB | Add `display_name`, `title_generated_at` to `agent_conversations` via migration | @codex | ⏳ |
| A2 | Domain | Plumb fields through ORM mappers and domain records | @codex | ⏳ |

### Workstream B – Title Service & Streaming

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Service | Implement internal `TitleService` using `gpt-5-mini`, short prompt | @codex | ⏳ |
| B2 | Trigger | Hook generation after first user message; idempotent update | @codex | ⏳ |
| B3 | SSE | Emit title in chat stream events; update streaming schemas | @codex | ⏳ |

### Workstream C – API Surface & Tests

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | API | Expose `display_name` on conversation summary/search/history responses | @codex | ⏳ |
| C2 | Tests | Unit tests for title service, mapper plumbing, SSE payload | @codex | ⏳ |
| C3 | Quality | `hatch run lint` and `hatch run typecheck` | @codex | ⏳ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Design | Confirm schema + service shape, streaming contract | Milestone doc updated, no code changes | ✅ | 2025-12-07 |
| P1 – Impl | Migration, service, wiring, API surface | Tests passing locally | ⏳ | 2025-12-09 |
| P2 – QA | Lint/typecheck, manual SSE smoke | Commands green, SSE emits title | ⏳ | 2025-12-10 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI Agents SDK available in backend environment; model `gpt-5-mini` accessible.
- Existing SSE infrastructure in `/chat/stream`.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Title generation delays stream | Med | Run asynchronously; cap timeout and length; emit only when ready. |
| DB migration conflicts | Low | Rebase on latest heads; use just task to generate migration. |
| Frontend not consuming new field | Low | Keep `topic_hint` fallback; document change. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- Unit tests for title service + SSE payload (new tests).
- Manual SSE smoke: call `/api/v1/chat/stream` and verify a title event arrives with `display_name` before stream close.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Apply DB migration via `just migrate` before deploying.
- No feature flags; fail-open if title generation fails.
- No backfill required; optional future script to title existing conversations.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-07 — Milestone drafted and approved; implementation pending.
