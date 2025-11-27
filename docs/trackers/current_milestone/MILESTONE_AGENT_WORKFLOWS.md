# Milestone: Agent Workflows (deterministic chains on top of Agents SDK)

Status: In Progress (backend API streaming added)
Owner: Platform Foundations
Goal: Add a first-class Workflow layer that sequences existing Agents SDK primitives deterministically (agent chains), without redefining "agent". Provide clean APIs and docs so operators can author, run, and observe workflows while keeping current agent catalog and handoff semantics intact.

## Phases

### Phase 1 — Design & contracts
- Write ADR covering terminology (Agent vs Workflow), constraints (no handoff agents inside strict chains unless explicitly allowed), and compatibility with existing AgentSpec/registry.
- Define `WorkflowSpec` dataclass + `WorkflowStep` shape (agent_key, input_mapper, guard, on_failure handling, max_turns override) in `app/workflows/specs.py`.
- Define `WorkflowDescriptor` + listing contract for APIs/UI.
- Update docs: `docs/integrations/openai-agents-sdk` add "Workflows" page with examples (triage+specialist chain, gated chain like `agent_chain.py`).

### Phase 2 — Backend implementation
- DONE: `app/workflows/` package with registry (spec discovery/validation), runner/service, sample `analysis_code` workflow.
- DONE: Streaming & sync APIs: `/api/v1/workflows` list, `/api/v1/workflows/{key}/run`, `/api/v1/workflows/{key}/run-stream` (SSE).
- DONE: Unit/contract tests for registry validation, runner guards/mappers, and API happy/error paths.
- DONE: Persist workflow runs/steps for auditability (tables, repo, recorder hook; responses carry `workflow_run_id`).

### Phase 3 — (Deferred) Frontend & operator UX
- Out of scope for this milestone per latest direction; keep API-only focus.

### Phase 4 — Docs, rollout, hardening
- Add runbook entry: how to create a workflow, regenerate SDK, and test locally (`just test-unit` focus on workflow suite).
- Lint/typecheck gates updated (`hatch run lint`, `hatch run typecheck`, `pnpm lint`, `pnpm type-check`).
- Definition of Done checklist (tests green, docs merged, examples added).

## Out of scope (for this milestone)
- Visual workflow builder UI; dynamic runtime-authored workflows; persisted workflow definitions in DB.
- Changing existing AgentSpec semantics or removing handoffs.

## Acceptance criteria
- New Workflow layer coexists with existing agents; no breaking changes to current `/agents` or chat APIs.
- A sample workflow (e.g., data_analyst → code_assistant with mapped input) runs end-to-end via API and emits per-step traces.
- Clear docs and examples show when to choose handoffs vs workflows.
