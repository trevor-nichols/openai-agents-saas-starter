# Milestone: Containers + Code Interpreter Integration (Backend + Agents)

Status: Completed
Owner: Platform Foundations (@codex)
Goal: Ship first-class container support for the Code Interpreter (python) tool so agents default to auto containers but can optionally bind explicit containers with full API-configurable options, tenant scoping, and clean observability.

## Phases

### Phase 1 — Data model & migration
- Add Alembic migration creating `containers` and `agent_containers` tables (UUID PK, openai_id, tenant_id, owner_user_id, name, memory_limit, status, expires_after JSON, last_active_at, metadata_json, timestamps, soft delete; composite PK on agent binding).
- Keep SQLite compatibility (JSONBCompat, index choices) and add unique `(tenant_id, name)`.

### Phase 2 — Service layer
- Implement `ContainerService` mirroring `VectorStoreService`: create/list/retrieve/delete containers via OpenAI API, enforce quotas/limits, soft-delete on failure, refresh status/last_active_at on access, and manage agent bindings.
- Support explicit + auto modes: helpers to resolve the active container for a tenant/agent; graceful fallback to auto when explicit binding is missing or expired.

### Phase 3 — Tool registry + Agent spec/runtime
- Extend tool registry to expose `code_interpreter_auto` (default) and `code_interpreter_explicit` (resolves bound container ID, else optional fallback to auto).
- Update `AgentSpec` to allow per-tool config (mode, memory tier, file_ids optional) and plumb runtime context (tenant/user) into tool factories.
- Validate missing required explicit bindings at agent build time when mode is forced.

### Phase 4 — API surface
- Add tenant-scoped `/api/v1/containers` CRUD endpoints plus optional file attach/list/download proxy if needed; error mapping aligned to OpenAI containers API.
- Add `/api/v1/agents/{agent_key}/container` bind/unbind endpoint scoped to tenant.
- Update tool catalog endpoint (if applicable) to reflect code interpreter availability and binding status.

### Phase 5 — Settings, quotas, observability
- Introduce settings for default auto memory tier, allowed explicit tiers, max containers per tenant, and bind fallback policy.
- Emit metrics/tracing around create/retrieve/delete/bind; structured logs with container_id/openai_id; update rate limits if needed.

### Phase 6 — Docs & examples
- Add runbook: when to use auto vs explicit, lifecycle/expiry expectations, file annotations, and binding workflow (API + dashboard if applicable).
- Document agent-spec changes and tool registry options; add example script mirroring vector-store example.

### Phase 7 — Testing & cutover
- Unit tests for service (happy/expiry/quota/duplicate name), API contract tests, and agent runtime resolution tests.
- Backfill changelog; move tracker to `complete/` on sign-off.

## Out of scope (for this milestone)
- Background worker to auto-refresh containers (can be added later if needed).
- Persisting container files locally (rely on OpenAI annotations + download endpoints).
- Frontend UX for container management (backend-first milestone).

## Definition of Done
- Migration applies cleanly in SQLite + Postgres; lint/typecheck pass (`hatch run lint`, `hatch run typecheck`).
- ContainerService operational with quota/error handling; agent binding supports auto default + explicit override.
- API endpoints available and documented; tool registry exposes both modes; agent specs can opt into explicit mode without code changes elsewhere.
- Metrics/tracing/logging in place for container lifecycle; docs/runbook updated; tests added for service/API/runtime resolution.

## Changelog
- **2025-11-26**: Phase 1 done — added containers + agent_containers tables, ORM models, service skeleton, Prometheus metrics, and tenant-scoped CRUD/bind API wiring.
- **2025-11-26**: Phase 2/3/4 completed — ContainerService cache + bindings, container settings/quotas, code interpreter auto tool registration, agent runtime passes container bindings; tool selection honors explicit/auto modes with fallback policy.
- **2025-11-26**: Phase 6 docs shipped — runbook `docs/runbooks/agents/containers-and-code-interpreter.md` covering modes, API, settings, binding, and risks.
- **2025-11-26**: Phase 7 sign-off — implementation complete; lint & typecheck green; migrations applied with merge head; cache invalidation on container delete fixed.
