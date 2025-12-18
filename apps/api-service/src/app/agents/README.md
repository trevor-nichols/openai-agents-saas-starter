# Agents package

Operational guide for declaring and running agents with the OpenAI Agents SDK inside the API service. Keep this as the single source of truth for how we build specs, prompts, tools, handoffs, and outputs.

## Mental model
- **Declarative specs → concrete SDK Agents at runtime.** Specs live in `app/agents/<key>/spec.py`; `OpenAIAgentRegistry` renders prompts with request context and attaches tools/handoffs on each call.
- **Explicit tools only.** If a tool isn’t named in `tool_keys`, it is not exposed. Optional tools (e.g., `web_search`) are skipped quietly when unavailable; required tools cause startup errors.
- **Handoffs are first-class.** Orchestrator agents list `handoff_keys`; input filters and per-target overrides tune what history/shape flows to the next agent.
- **Models are explicit and predictable.** Specs can set `model` (fixed per-agent) or use `model_key` (settings bucket). Otherwise they use `AGENT_MODEL_DEFAULT`.

## AgentSpec fields (TL;DR)
- Identity & model: `key` (dir name), `display_name`, `description`, optional `model` (spec default), optional `model_key` (→ settings bucket), `capabilities` (catalog metadata), `default` (provider default).
- Prompt: `prompt_path` **or** `instructions` (Jinja allowed), `wrap_with_handoff_prompt`, `prompt_defaults`.
- Tools: `tool_keys` (ordered, explicit) + `tool_configs` (per-tool knobs).
- Handoffs: `handoff_keys`, `handoff_context` (`full`|`fresh`|`last_turn`), `handoff_overrides` (tool_name/description, input_filter, input_type, is_enabled).
- Agents-as-tools: `agent_tool_keys`, `agent_tool_overrides` (tool_name/description, custom_output_extractor, is_enabled, run_config, max_turns).
- Retrieval: `vector_store_binding` (`tenant_default`|`static`|`required`), optional `vector_store_ids`, `file_search_options` (max_num_results, filters, ranking_options, include_search_results).
- Outputs & validation: `output` (text | json_schema via `type_path` or `custom_schema_path`), `guardrails`, `tool_guardrails`, `tool_guardrail_overrides`, `guardrails_runtime` (suppress_tripwire, streaming_mode, concurrency, result_handler_path).
- Memory defaults: `memory_strategy` (defaults applied after per-request and per-conversation overrides; supports trim/summarize/compact, token budgets, compact rules).
- Misc: `prompt_defaults` feed prompt rendering; `capabilities` are surfaced in catalogs.

## Tool inventory (where tools come from)
- Registry (`app/utils/tools/registry.py::initialize_tools()`): registers hosted OpenAI tools (`web_search`, `code_interpreter`, `image_generation`, `file_search`) when `OPENAI_API_KEY` is set, plus hosted MCP tools from `mcp_tools` settings.
- Built-in utility tools: `OpenAIAgentRegistry._register_builtin_tools()` adds `get_current_time` and `search_conversations`.
- Agent-as-tools: any agent listed in `agent_tool_keys` is exposed via `as_tool`.
- Custom function tools: register in the tool registry and list the tool name in `tool_keys` to expose it on an agent.
## Patterns & examples

### 1) Simple single-agent
```
def get_agent_spec() -> AgentSpec:
    base = Path(__file__).parent
    return AgentSpec(
        key="faq",
        display_name="FAQ Helper",
        description="Answers product FAQs from conversation search + web",
        model_key=None,  # use agent_default_model
        tool_keys=("search_conversations", "web_search", "get_current_time"),
        prompt_path=base / "prompt.md.j2",
    )
```

### 2) Orchestrator with handoffs
```
def get_agent_spec() -> AgentSpec:
    base = Path(__file__).parent
    return AgentSpec(
        key="triage",
        display_name="Triage Assistant",
        description="Routes to specialists; keep answers brief.",
        model_key="triage",
        tool_keys=("web_search", "search_conversations"),
        prompt_path=base / "prompt.md.j2",
        handoff_keys=("code_assistant", "researcher"),
        wrap_with_handoff_prompt=True,
        handoff_context={"code_assistant": "last_turn", "researcher": "fresh"},
        handoff_overrides={
            "researcher": HandoffConfig(
                tool_name="handoff_to_data",
                input_filter="remove_all_tools",
            )
        },
    )
```

### 3) Agents as tools (vs handoffs)
- Use `agent.as_tool(...)` when you want the parent agent to remain in control and treat the sub-agent as a function call (parent continues the conversation).
- Use handoffs when you want the sub-agent to take over the conversation flow and inherit (filtered) history.
- In specs we favor **handoffs for ownership transfer**, **tools for short, encapsulated sub-tasks**.

Example spec snippet:

```
from app.agents._shared.specs import AgentSpec, AgentToolConfig

return AgentSpec(
    key="translator",
    ...,
    agent_tool_keys=("spanish_agent", "french_agent"),
    agent_tool_overrides={
        "spanish_agent": AgentToolConfig(tool_name="translate_to_spanish"),
    },
)
```

### 4) Structured outputs
```
from app.schemas.analytics import Insights  # Pydantic model

return AgentSpec(
    key="insights",
    ...,
    output=OutputSpec(
        mode="json_schema",
        type_path="app.schemas.analytics:Insights",
        strict=True,  # Structured Outputs
    ),
)
```
- For bespoke schemas/validation, set `custom_schema_path` to an `AgentOutputSchemaBase` subclass.

### 5) Tool configuration knobs
- **Code Interpreter**
  - Default registration uses auto containers with `settings.container_default_auto_memory`.
  - Per-agent override via `tool_configs={"code_interpreter": {"mode": "explicit", "container_id": "...", "file_ids": [...], "memory_limit": "2g"}}`.
  - If `mode="explicit"` and no container binding is found, we error unless `settings.container_fallback_to_auto_on_missing_binding` is True.
  - Container resolution: InteractionContextBuilder pulls per-tenant agent→container bindings from `ContainerService`; if `container_id` is set in `tool_configs`, it is used; otherwise auto mode provisions/uses OpenAI-managed containers with the default memory limit.
- **Image generation**
  - Override size/quality/format/background/compression/partial_images via `tool_configs={"image_generation": {...}}`.
  - Validation enforced in `ToolResolver._validate_image_config` (size/quality/background/format/compression/partial_images).
- **Web search**
  - Inherits user_location from `PromptRuntimeContext` when available; no per-agent config today.
- **File search / vector stores**
  - Use `vector_store_binding="tenant_default"` (preferred) or `vector_store_binding="static"` with explicit `vector_store_ids` (tuple of IDs).
  - `vector_store_binding="required"` fails if no tenant binding is resolved.
  - Pass per-agent `file_search_options` (max_num_results, filters, ranking_options, include_search_results) to FileSearchTool.
  - Resolution order at runtime (InteractionContextBuilder):
    1) Request override (`vector_store_ids`/`vector_store_id`).
    2) Agent-to-store binding from DB (VectorStoreService binding).
    3) Spec config: `static` requires `vector_store_ids`; `required` demands an existing primary; `tenant_default` resolves or auto-creates the tenant primary (if enabled).
  - See `app/services/vector_stores/README.md` for binding APIs and store management.

## Prompt authoring
- Prefer `prompt.md.j2`; keep logic minimal and declarative.
- Always-available context keys (when runtime context exists):
  - `user.id`, `tenant.id`, `agent.key/display_name`, `run.conversation_id`, `run.request_message`, `env.environment`, `memory.summary`
  - `date`, `time`, `date_and_time`
- Add static variables via `prompt_defaults` in the spec.
- Add dynamic variables by registering a provider in `_shared/prompt_context.py`. Provider keys are injected globally, so keep them lightweight and deterministic.
- Jinja runs with `StrictUndefined` at request time.

## Handoff controls (input_filter shortcuts)
- `full` (default) – pass entire history.
- `fresh` – drop history.
- `last_turn` – keep last 1–2 turns.
- `remove_all_tools` – strips tool messages (from SDK handoff_filters).
- Use `handoff_overrides[input_filter="name"]` to apply a specific filter per target.
- `input_type` can point to a Pydantic model/dataclass to validate handoff args.

## Guardrails
- `guardrails` apply input/output guardrails to the agent (built via GuardrailBuilder).
- `tool_guardrails` apply guardrails to all tools; `tool_guardrail_overrides` can disable or replace per tool.
- `guardrails_runtime` controls behavior (suppress tripwire, streaming vs blocking, concurrency, result handler).
- See `app/guardrails/README.md` and `docs/integrations/openai-agents-sdk/guardrails/` for supported configs and tripwire behaviors.

## Memory defaults
- `memory_strategy` lets you set agent-level defaults for trim/summarize/compact (token budgets, compact_keep, clear_tool_inputs, include/exclude tools).
- Precedence: request > conversation defaults > agent defaults.
- Summaries can persist via `StrategySession` when using `SUMMARIZE`; compact events surface as lifecycle stream events.

## Adding tools
1) Implement a function tool with `@function_tool` (can accept `RunContextWrapper` as first arg).
2) Register it in `app/utils/tools/registry.py::initialize_tools()` with a stable name.
3) Reference the name in `tool_keys` of any agent spec.

### Adding hosted MCP tools (remote MCP servers or OpenAI connectors)
- Configure the tool via settings (supports JSON env):
  - Example: `MCP_TOOLS='[{"name":"repo_mcp","server_label":"gitmcp","server_url":"https://gitmcp.io/openai/codex","require_approval":"always"}]'`
  - For connectors, use `connector_id` plus `authorization` instead of `server_url`.
- On startup `initialize_tools()` registers each entry as a `HostedMCPTool`; add the `name` to any agent’s `tool_keys` to expose it.
- Defaults are safe: `require_approval` defaults to `"always"`; validations enforce unique names and exactly one of `server_url` or `connector_id`.
- Optional policy knobs per tool: `auto_approve_tools` (allow-list), `deny_tools` (block-list, wins over allow). Unlisted tool names are denied by default via the registry’s approval handler.

## Runtime knobs (per request)
- `AgentChatRequest.run_options` maps to `RunOptions` → `agents.Runner`:
  - `max_turns`, `previous_response_id`
  - `run_config` keys: `model_settings`, `input_guardrails`, `output_guardrails`, `tracing_disabled`, `trace_include_sensitive_data`, `workflow_name` (model overrides are intentionally not accepted)
  - `handoff_input_filter` (global, name resolved via `_shared/handoff_filters`)
  - `handoff_context_policy` (alias for the common filters: `full`/`fresh`/`last_turn`)
- Streaming vs sync: `chat_stream` uses `run_stream` and emits `AgentStreamEvent` (raw deltas, run items, lifecycle); `chat` uses `run`.

## Adding a new agent (checklist)
- [ ] Create folder `app/agents/<key>/`; add `spec.py`, `prompt.md.j2`.
- [ ] Set `tool_keys` (and `tool_configs` if needed); ensure tools are registered.
- [ ] Add `handoff_keys`/`handoff_context` if orchestrating; update targets’ specs first to satisfy topo order.
- [ ] Decide output mode (`output`).
- [ ] Add prompt defaults/context providers as needed.
- [ ] Run `hatch run lint` + `hatch run typecheck`.
- [ ] (Optional) Add contract tests under `tests/contract/test_agents_api.py` for catalog shape/output.

## Troubleshooting
- “tool not registered” → add to `initialize_tools()` or fix `tool_keys`.
- Handoff cycle errors → check `handoff_keys` ordering; specs must be DAG.
- Structured output errors → ensure `type_path` points to importable class and all schema fields are required (Structured Outputs requirement).
- Code interpreter “explicit container required” → bind container or switch mode to `auto`.

## Reference
- SDK docs: `docs/integrations/openai-agents-sdk/`
- Provider layer: `app/infrastructure/providers/openai/`
- Runtime adapters: `app/infrastructure/providers/openai/runtime.py`
- Spec primitives: `app/agents/_shared/specs.py`
