<!-- SECTION: Metadata -->
# Milestone: Productionize Agent Long-Term Memory

_Last updated: 2025-12-07_  
**Status:** In Progress  
**Owner:** @platform-foundations  
**Domain:** Backend  
**ID / Links:** [Docs](../../integrations/openai-agents-sdk/memory/long_term_memory_strategies/README.md), [Design notes](../../integrations/openai-agents-sdk/memory/long_term_memory_strategies/agent_service/README.md)

---

<!-- SECTION: Objective -->
## Objective

Deliver production-grade long-term memory for OpenAI Agents: high-quality summarization, token-aware triggering, durable cross-session hygiene, and smarter compaction with observability—aligned to the documented strategies and configurable via agent specs.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Summarization uses a real model (default GPT-5.1 medium reasoning) with config override per agent spec; summaries persisted with metadata and size guards.
- Token-first triggers drive trim/summarize/compact decisions using percentage-of-window thresholds and token estimates; trigger reason is recorded.
- Compaction differentiates tool inputs vs outputs, applies exclusion policies, and emits richer placeholders plus telemetry.
- Cross-session memory injection selects the freshest valid summary with staleness/size checks; no stale or oversized injections.
- Workflow runner adopts the same memory strategy surface as chat (or explicitly noted out of scope here).
- Metrics/logs cover tokens_before/after, trigger_reason, summary length, compaction counts; alerts for summarizer failures.
- Evaluation harness covers summary fidelity and post-compaction Q/A success.
- `hatch run lint` / `hatch run typecheck` / relevant tests pass.
- Docs/trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Production summarizer layer (default model + per-agent override).
- Token-first strategy triggers (hard/soft thresholds, % window).
- Compaction polish (inputs vs outputs, exclusion lists, richer placeholders).
- Cross-session memory hygiene (freshness, size caps, selection rules).
- Telemetry and validation (metrics, logs, config validation).
- Evaluation harness for memory behaviors.

### Out of Scope
- Workflow memory parity rollout details (tracked but sequenced after core impl).
- Any non-OpenAI provider support.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⚠️ | Token-first + hygiene patterns defined; workflow parity design deferred. |
| Implementation | ⏳ | Core summarizer/token/compaction/hygiene shipped; telemetry hooked; workflow parity pending. |
| Tests & QA | ⚠️ | Lint/typecheck green; memory strategy unit suite passing; eval harness still pending. |
| Docs & runbooks | ⏳ | Milestone updated; spec config doc added; impl docs to follow. |

---

<!-- SECTION: Architecture / Design Snapshot -->
## Architecture / Design Snapshot

- Existing surface: `MemoryStrategyConfig` (`none/trim/summarize/compact`) wraps provider sessions via `StrategySession`; compaction emits lifecycle events; summaries persisted via `persist_summary`; cross-session injection loads latest summary into prompt context.
- Gaps vs docs: no real summarizer (Noop), trim/summarize are turn-based only, workflow runner bypasses strategies, memory injection lacks freshness/size policy, compaction placeholders are generic, telemetry minimal.
- Target design: plug a production summarizer (default GPT-5.1 medium reasoning) with per-agent spec override; token-first policy selecting trim/summarize/compact based on % of context; richer compaction with input/output handling and exclusions; cross-session selection with staleness + size guards; unified metrics; extend same surface to workflows.

### Decisions (2025-12-07)
- Summarizer: default GPT-5.1 medium reasoning; max summary size enforced in system prompt; centralized retry/backoff acceptable (implement shared policy).
- Token triggers: default hard trigger at 20% context remaining (from 400k window); allow agent-spec override of thresholds.
- Cross-session hygiene: freshness window 14 days and 4k-char cap; skip injection if no valid summary passes guards.
- Compaction: default apply to all tools; allow agent-spec override for exclusions; placeholders stay simple but include tool name/call id/kind.
- Workflow parity: deferred, but implementation must stay extensible for workflows later.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Production Summarizer & Injection

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Runtime | Add GPT-5.1 medium summarizer adapter behind `Summarizer` with retries/limits | @platform-foundations | ✅ |
| A2 | Config | Per-agent spec override for summarizer model/params; safe defaults | @platform-foundations | ✅ (documented; wired through descriptors) |
| A3 | Persistence | Persist summary metadata (model, tokens, created_at, size cap) | @platform-foundations | ✅ (model + version + length tokens persisted) |
| A4 | Injection | Freshness/size-checked selection; reject stale/oversized summaries | @platform-foundations | ✅ |

### Workstream B – Token-First Triggers & Strategy Selection

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Policy | Compute context-left % (default 400k window) and soft/hard thresholds | @platform-foundations | ✅ (hard 20% default wired) |
| B2 | Runtime | Route to trim/summarize/compact based on thresholds; record trigger_reason | @platform-foundations | ✅ (token triggers applied) |
| B3 | Telemetry | Emit metrics for tokens_before/after, % remaining, chosen strategy | @platform-foundations | ✅ (tokens_before/after + triggers recorded) |

### Workstream C – Smarter Compaction

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Policy | Separate handling for tool inputs vs outputs; exclusion/retention lists | @platform-foundations | ✅ (inputs/outputs split, include/exclude supported) |
| C2 | UX | Rich placeholders (tool name, call id, kind, reason) | @platform-foundations | ⏳ (placeholders simple; kind present; future polish) |
| C3 | Telemetry | Compaction event payloads include retained/removed counts and reasons | @platform-foundations | ✅ (counts added; metrics/logs wired) |

### Workstream D – Cross-Session Memory Hygiene

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Selection | Choose freshest valid summary per agent; enforce staleness/size caps | @platform-foundations | ✅ (14d freshness, 4k cap enforced at injection) |
| D2 | Storage | Clarify/store summary provenance in DB (existing conversation summaries) | @platform-foundations | ✅ (model/version/length tokens persisted; migration applied) |
| D3 | Safety | Fallback when no valid summary (skip injection, log) | @platform-foundations | ✅ (skip + log reason) |

### Workstream E – Evaluation Harness

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | Tests | Add evals for summary fidelity and post-compaction Q/A success | @platform-foundations | ⏳ |
| E2 | CI | Wire evals or targeted suites into CI smoke for memory paths | @platform-foundations | ⏳ (unit coverage added; memory suite now passing; eval wiring pending) |

### Workstream F – Workflow Parity (Deferred)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| F1 | Runtime | Apply memory strategies to workflow runner sessions | @platform-foundations | ⏳ |
| F2 | Telemetry | Project workflow compaction/summarization events into run logs | @platform-foundations | ⏳ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Finalize policies (models, thresholds, injection rules) | Decisions recorded; milestone doc updated | ⏳ | 2025-12-12 |
| P1 – Core Impl | Summarizer, token triggers, smarter compaction, hygiene | Unit/integration tests pass; telemetry in place | ⏳ | 2025-12-22 |
| P2 – Parity & Evals | Workflow parity, eval harness, docs | Eval green; CI gates on core suites | ⏳ | 2026-01-05 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI GPT-5.1 (reasoning) availability for summarization.
- Conversation summary storage (existing DB tables) accessible for injection.
- Observability stack for metrics/logging.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Summaries bloat prompts | Medium | Enforce size caps, truncate, reject stale/oversized summaries. |
| Token estimates drift | Medium | Use conservative thresholds and soft/hard bands; add telemetry to tune. |
| Compaction removes needed data | High | Input/output split, exclusion lists, richer placeholders, evals. |
| Model dependency flakiness | Medium | Retries/backoff; allow model override per agent. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `hatch run lint`, `hatch run typecheck`, targeted pytest suites for memory strategy paths.
- Unit tests for token-trigger routing, summarizer adapter, compaction policies.
- Scenario/eval tests: answer correctness after summarization/compaction; injection staleness checks.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Defaults: GPT-5.1 medium summarizer, soft/hard % thresholds (e.g., 30%/20% context left), safe compaction placeholders.
- Agent spec can override summarizer model/params and thresholds; request-level can still override.
- Logs/metrics emit trigger_reason and deltas for tuning; enable alerts on summarizer failures.
- Workflow parity rollout deferred; track separately before enabling.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-07 — Memory strategy unit suite passing; lint/typecheck green; token/compaction metrics validated.
- 2025-12-07 — Initial milestone draft capturing gaps and target plan.

