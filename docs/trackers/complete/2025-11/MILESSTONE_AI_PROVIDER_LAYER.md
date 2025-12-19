# AI Provider Layer Refactor Milestone

**Status:** Completed – November 19, 2025  
**DRI:** Platform Foundations (TBD)  
**Stakeholders:** App Platform, Frontend Core, Starter CLI  
**Related Docs:** `api-service/SNAPSHOT.md`, `docs/openai-agents-sdk/*`

## Objective

Create a provider-agnostic AI orchestration layer so new OpenAI (Agents, Realtime, Guardrails) and future vendor APIs can be added without touching domain services or HTTP routes.

## Success Criteria

- Domain services depend only on provider-neutral ports (`AgentRuntime`, `SessionStore`, `GuardrailPolicyStore`, `RealtimeChannelFactory`, `ToolRegistryPort`).
- OpenAI provider lives entirely under `app/infrastructure/providers/openai/**` with clear surface folders (`agents/`, `realtime/`, `guardrails/`).
- FastAPI startup + CLI bootstrap configure providers declaratively (single registry entry point) and tests can inject fakes without monkeypatching globals.
- Documentation (`SNAPSHOT.md`, SDK docs) describes how to add a new provider or OpenAI surface.

## Non-Goals

- Shipping additional provider implementations beyond OpenAI in this milestone.
- Rewriting the frontend data flow; only backend contracts change.
- Replacing existing persistence (Postgres/Redis) patterns.

## Timeline & Phases

| Phase | Target Date | Owner | Deliverables | Status |
| --- | --- | --- | --- | --- |
| 1. Domain Ports & Models | Nov 26, 2025 | Backend Eng | `app/domain/ai/ports.py`, capability/value objects, unit tests | Completed – Nov 19, 2025 |
| 2. Provider Registry & Config | Dec 3, 2025 | Platform Foundations | `app/services/agents/provider_registry.py`, settings updates, bootstrap wiring | Completed – Nov 19, 2025 |
| 3. OpenAI Adapter Extraction | Dec 10, 2025 | Backend Eng | `app/infrastructure/providers/openai/**` (agents runtime, session store, guardrails, realtime stubs) + integration tests | Completed – Nov 19, 2025 |
| 4. Service Layer Integration | Dec 15, 2025 | Backend Eng + QA | Refactored `AgentService`, updated routers, contract tests (`tests/contract/chat`) passing | Completed – Nov 19, 2025 |
| 5. Docs & Ops Hardening | Dec 18, 2025 | Platform Foundations + Docs | Updated `SNAPSHOT.md`, SDK guides, tracker closeout checklist | Completed – Nov 19, 2025 |

## Workstream Details

### 1. Domain Ports & Capability Descriptors
- Define provider-neutral protocols and dataclasses under `app/domain/ai/`.
- Ensure conversation services consume only these interfaces.
- Add unit tests covering fake runtimes + tool registries.

### 2. Provider Registry & Bootstrap
- Introduce registry pattern with named providers and selection logic (default, tenant-scoped future hooks).
- Extend `app/core/settings/__init__.py` with `OpenAISettings` + provider enablement map.
- Wire FastAPI startup + CLI to register providers via bootstrap module.

### 3. OpenAI Adapter Extraction
- Move current `infrastructure/openai/runner.py` and `sessions.py` into provider-specific modules that implement the new ports.
- Add guardrails + realtime folders even if they export thin placeholders to establish structure.
- Ensure adapters handle telemetry, retries, and usage propagation locally.

### 4. Service Layer Integration
- Update `AgentService` to depend on the provider registry + domain ports.
- Remove direct imports of `agents` SDK from service or API layers.
- Refresh contract/integration tests, ensuring SQLite + fakeredis paths still pass.

### 5. Documentation & Operational Updates
- Regenerate `api-service/SNAPSHOT.md` sections affected by new folders.
- Update `docs/openai-agents-sdk/*` with provider extension steps.
- Capture migration notes (any env var rename, table changes) and communicate to Starter CLI for provisioning scripts.

## Dependencies

- Settings changes must land alongside Starter CLI updates so `just bootstrap` emits the new env vars.
- Any SQLAlchemy session table migration requires Alembic revision; coordinate with Database team.
- Observability changes (new metrics/traces) must align with `docs/observability.md` guidelines.

## Risks & Mitigations

- **Scope Creep:** Adding non-OpenAI providers mid-milestone would delay delivery. Mitigation: Lock scope via this tracker and defer extra providers to a follow-up.
- **Regression Surface:** Moving runtime logic can break chat streaming. Mitigation: expand contract tests + add provider-focused unit tests with mocks.
- **Configuration Drift:** New settings may not propagate to CLI or infra. Mitigation: tie each config change to `starter_cli/README.md` update before merge.

## QA / Validation Plan

- Unit tests for domain ports (fake implementations) executed via `hatch run test-domain-ai` (new or existing target).
- Existing FastAPI contract tests (`tests/contract/chat/test_chat.py`) and streaming tests must pass without mocks.
- Add smoke test to Starter CLI to ensure provider registry initializes without server imports.

## Exit Criteria

- Provider registry + ports merged and used by runtime code paths.
- OpenAI provider isolated, and no other layer imports `agents.*` directly.
- Documentation + tracker updated to "Complete" with references to merged PRs.
