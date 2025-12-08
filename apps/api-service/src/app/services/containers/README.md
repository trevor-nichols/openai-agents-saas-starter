# Containers service (Code Interpreter)

Manages OpenAI containers for the Code Interpreter tool and binds them to agents per tenant.

## What lives here
- `service.py` — create/list/get/delete containers (OpenAI API + DB), bind/unbind agents to containers, resolve bindings, enforce quotas and allowed memory tiers.
- Persistence models live under `app/infrastructure/persistence/containers/`.

## How it ties to AgentSpec
- The `code_interpreter` tool is registered with auto containers by default. In an AgentSpec, `tool_configs={"code_interpreter": {"mode": "explicit", "container_id": "...", "file_ids": [...], "memory_limit": "2g"}}` can request explicit containers.
- At runtime, `InteractionContextBuilder` fetches agent→container bindings from ContainerService and passes them into `PromptRuntimeContext.container_bindings`.
- Resolution order:
  1) If `tool_configs.container_id` is set, that explicit OpenAI container ID is used.
  2) Else, if the tenant has an agent binding in ContainerService, that binding is used.
  3) Else, auto mode uses OpenAI-managed containers with the default memory limit (`settings.container_default_auto_memory`).
- If `mode="explicit"` and no binding/ID exists, runtime errors unless `settings.container_fallback_to_auto_on_missing_binding` is True.

## Key behaviors
- Quotas: enforced per tenant via `container_max_containers_per_tenant` and allowed memory tiers (`container_allowed_memory_tiers`).
- Cleanup: delete removes remote container and marks local record deleted.
- Bindings: `bind_agent_to_container`, `unbind_agent_from_container`, `resolve_agent_container_openai_id`, and `list_agent_bindings` (used by InteractionContextBuilder).

## When to touch this
- Changing container quota/memory rules, binding behavior, or explicit/auto resolution defaults.
- Adjusting how container deletions are propagated to OpenAI or local state.

## References
- Agent tool config: `app/agents/README.md` (Code Interpreter section).
- Runtime binding resolution: `app/services/agents/interaction_context.py`.
