# Containers + Code Interpreter Runbook

Last updated: November 26, 2025

## Why
The Code Interpreter (python) tool always runs inside an OpenAI container. We ship auto containers by default but allow explicit, tenant-scoped containers with controllable memory tier, seeded files, and agent bindings.

## Modes
- **Auto (default)**: tool_config `{type: "code_interpreter", container: {type: "auto", memory_limit: <settings.container_default_auto_memory>}}`. Created/reused automatically; no DB record.
- **Explicit**: provision via `/api/v1/containers` (name + memory_limit + optional expires_after/file_ids). Bind to an agent with `/api/v1/agents/{agent_key}/container`. The runtime injects the bound `container_id`; if absent, fallback to auto is governed by `container_fallback_to_auto_on_missing_binding`.

## Settings (app/core/settings/ai.py)
- `container_default_auto_memory`: default tier for auto containers (1g/4g/16g/64g).
- `container_allowed_memory_tiers`: allowed tiers for explicit containers.
- `container_max_containers_per_tenant`: quota for explicit containers.
- `container_fallback_to_auto_on_missing_binding`: if false, explicit mode without binding raises.

## API surface
- `POST /api/v1/containers` — create explicit container (name, memory_limit, expires_after?, file_ids?, metadata?).
- `GET /api/v1/containers` — list tenant containers.
- `GET /api/v1/containers/{id}` — fetch metadata.
- `DELETE /api/v1/containers/{id}` — delete (soft-delete locally, delete remote).
- `POST /api/v1/agents/{agent_key}/container` — bind agent → container.
- `DELETE /api/v1/agents/{agent_key}/container` — unbind.

## Agent spec wiring
In `AgentSpec`, use `tool_keys=("code_interpreter", ...)` and optional `tool_configs`:

```python
AgentSpec(
    key="data_analyst",
    tool_keys=("code_interpreter",),
    tool_configs={
        "code_interpreter": {
            "mode": "explicit",           # or "auto" (default)
            "memory_limit": "4g",         # applies to auto containers; explicit uses bound container's tier
            "file_ids": ["file-abc123"],   # optional seed files for auto
            # "container_id": "cntr_...", # overrides binding (rare)
        }
    },
)
```

Runtime resolution (OpenAIAgentRegistry):
- If `mode=explicit` and a binding exists for the tenant/agent, injects `container_id`.
- If `mode=explicit` but missing binding: fallback to auto when `container_fallback_to_auto_on_missing_binding=True`; otherwise raises.
- If `mode=auto`, builds auto container config; honors `memory_limit`/`file_ids` from `tool_configs`.

## Persistence & quotas
- Tables: `containers`, `agent_containers` (tenant-scoped, unique name per tenant, soft-delete). No local storage of container files (ephemeral by design).
- Quotas: enforced in `ContainerService` using settings above; memory tiers validated against allow-list.

## Metrics & observability
- Prometheus: `container_operations_total{operation,result}` and `container_operation_duration_seconds` for create/list/get/delete.
- Structured logs: `container.create.failed`, `container.delete.failed`, cleanup warnings.

## Expiry semantics (OpenAI platform)
- Containers expire after 20 minutes of inactivity (default anchor last_active_at). Access/updates refresh `last_active_at` remotely. Expired containers cannot be reactivated; create a new one and rebind.

## Typical flows
1) Auto-only (default)
   - Add `code_interpreter` to agent `tool_keys` (no further config). Model receives auto container.
2) Explicit, reusable
   - `POST /containers` with `memory_limit: "16g"`.
   - `POST /agents/{agent_key}/container` with returned `id`.
   - Agent runs use that container; if it expires, create/rebind.

## Risks / notes
- Do not persist container files locally; download via OpenAI if needed while active.
- If `container_fallback_to_auto_on_missing_binding` is false, ensure bindings exist before enabling explicit mode on an agent to avoid runtime failures.
- Keep names tenant-unique; duplicates fail with HTTP 409.
