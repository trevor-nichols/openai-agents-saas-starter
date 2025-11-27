# ADR: Introduce Workflow Layer on top of Agents SDK

- Status: Accepted (2025-11-27)
- Context: We use OpenAI Agents SDK. Agents are code-defined `AgentSpec` instances with tools/handoffs. Users request deterministic “agent chains” (see SDK example `agent_chain.py`). We need to support repeatable pipelines without redefining “agent” or persisting agents in DB.

## Decision
Add a first-class Workflow layer that sequences existing agents deterministically. Workflows are discovered from code specs (no DB persistence), have their own catalog/API, and reuse the existing agent registry/runtime for each step. Agents remain single-responsibility units; workflows orchestrate them.

## Terminology
- Agent: One SDK `Agent` built from `AgentSpec` with tools/handoffs; listed at `/api/v1/agents`.
- Workflow: Deterministic sequence/branching over agents; listed at `/api/v1/workflows`; executed via runner with per-step guards.
- Handoff: Runtime delegation between agents inside a single agent run. Allowed inside agents; optionally disallowed inside strict workflows.

## Constraints
- Do not persist agents or workflows in DB for this milestone.
- Workflows must reference existing agent keys; validation fails otherwise.
- Optional mode to forbid agents that already declare handoffs in linear workflows to keep chains deterministic.
- Prompt/runtime context must be rebuilt per step using `PromptRuntimeContext` (tenant/user/location/container bindings).
- Tracing/metrics must include workflow name and step.

## Alternatives considered
1) Redefine “agent” to mean an entire pipeline. Rejected: large refactor, loses modularity and observability per step.
2) Keep only handoffs. Rejected: handoffs are dynamic routing, not deterministic chains with guards.

## Consequences
- New `app/workflows` package (specs, registry, runner, service) plus `/api/v1/workflows` endpoints.
- Frontend/SDK additions for listing/running workflows.
- Documentation updates to clarify when to choose workflows vs handoffs.
