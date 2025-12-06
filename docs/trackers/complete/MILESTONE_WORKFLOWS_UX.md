# Milestone: Workflows UX Backfill (API surface + SDK)

Status: Completed ✅  
Owner: Platform Foundations (backend)  
Goal: Ship the workflow endpoints and contracts needed to unblock the new workflows UI/UX (run history, richer descriptors, control actions) and regenerate the frontend SDK.

## Scope & Phases

### Phase 1 — API surface (must-have)
- Add `GET /api/v1/workflows/runs` (tenant-scoped) with filters: `workflow_key`, `status`, `started_before/after`, optional `conversation_id`, pagination (`limit` + `cursor` or `offset`/`limit`). Response: lightweight list view (id, workflow_key, status, started/ended_at, user_id, conversation_id, step_count, duration_ms, final_output_text snippet).
- Domain/repo: extend `WorkflowRunRepository` with `list_runs(...)`; implement query + keyset pagination in `SqlAlchemyWorkflowRunRepository`; add indexes on `(tenant_id, workflow_key, started_at desc)` and `(tenant_id, status, started_at desc)`.
- Schemas: add list view Pydantic models in `api/v1/workflows/schemas.py`; update OpenAPI.
- Tests: unit for repo pagination/filtering; contract tests for list endpoint (auth, tenant isolation).

### Phase 2 — Workflow descriptors (nice-to-have, UI unblocker)
- Add `GET /api/v1/workflows/{workflow_key}` returning descriptor + stages/steps/agents/max_turns/reducers/handoff flags from the registry (no DB hit).
- Update OpenAPI + add contract test.

### Phase 3 — Controls & streaming polish (optional but recommended)
- Add `POST /api/v1/workflows/runs/{run_id}/cancel` (marks run/steps cancelled, signals runner if active) and optional `POST /api/v1/workflows/runs/{run_id}/retry` if business rules allow.
- SSE tweaks: include `id:` and `event:` fields, server `timestamp`, and heartbeat comments (~15s) for proxy keep-alive; reflect in schema/docs.

### Phase 4 — SDK regeneration & wiring
- Export updated OpenAPI (`python -m starter_cli.app api export-openapi …`) and regenerate HeyAPI client (`cd web-app && pnpm generate:fixtures`).
- Verify the four existing endpoints plus new ones are present in `sdk.gen.ts` and `types.gen.ts`.

## Definition of Done
- New endpoints deployed and passing contract tests; indexes applied via Alembic migration.
- OpenAPI reflects list/detail/cancel (and optional retry) plus SSE metadata fields.
- Frontend SDK regenerated with zero type errors (`pnpm lint && pnpm type-check`).
