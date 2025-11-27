# Agents package

Operational guide for declaring and running agents with the OpenAI Agents SDK inside the API service. Keep this as the single source of truth for how we build specs, prompts, tools, handoffs, and outputs.

## Mental model
- **Declarative specs → concrete SDK Agents at runtime.** Specs live in `app/agents/<key>/spec.py`; `OpenAIAgentRegistry` renders prompts with request context and attaches tools/handoffs on each call.
- **Explicit tools only.** If a tool isn’t named in `tool_keys`, it is not exposed. Optional tools (e.g., `web_search`) are skipped quietly when unavailable; required tools cause startup errors.
- **Handoffs are first-class.** Orchestrator agents list `handoff_keys`; input filters and per-target overrides tune what history/shape flows to the next agent.
- **Settings select models.** `model_key` chooses `settings.agent_<key>_model`; otherwise `agent_default_model`.

## AgentSpec fields (TL;DR)
- `key` (dir name), `display_name`, `description`
- `model_key` → settings override; else default model
- `prompt_path` **or** `instructions` (Jinja allowed)
- `tool_keys` (ordered) + `tool_configs` (per-tool tweaks)
- `handoff_keys` + `handoff_context` (`full`|`fresh`|`last_turn`)
- `handoff_overrides` (tool_name/description, input_filter, input_type, is_enabled)
- `wrap_with_handoff_prompt` (adds SDK handoff prelude)
- `prompt_context_keys`, `prompt_defaults`, `extra_context_providers`
- `output` (text | json_schema, strict flag, custom schema path)
- `default` (provider default)

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
        prompt_context_keys=("user", "tenant", "run", "env"),
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
        handoff_keys=("code_assistant", "data_analyst"),
        wrap_with_handoff_prompt=True,
        handoff_context={"code_assistant": "last_turn", "data_analyst": "fresh"},
        handoff_overrides={
            "data_analyst": HandoffConfig(
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
- **Image generation**
  - Override size/quality/format/background/compression/partial_images via `tool_configs={"image_generation": {...}}`.
  - Validation enforced in `OpenAIAgentRegistry._validate_image_config`.
- **Web search**
  - Inherits user_location from `PromptRuntimeContext` when available; no per-agent config today.

## Prompt authoring
- Prefer `prompt.md.j2`; keep logic minimal and declarative.
- Available context keys when you include them in `prompt_context_keys`:
  - `user.id`, `tenant.id`, `agent.key/display_name`, `run.conversation_id`, `run.request_message`, `env.environment`
  - Custom providers via `extra_context_providers` (register in `_shared/prompt_context.py`).
- `prompt_defaults` supply fallback values; Jinja runs with `StrictUndefined` at request time.

## Handoff controls (input_filter shortcuts)
- `full` (default) – pass entire history.
- `fresh` – drop history.
- `last_turn` – keep last 1–2 turns.
- `remove_all_tools` – strips tool messages (from SDK handoff_filters).
- Use `handoff_overrides[input_filter="name"]` to apply a specific filter per target.
- `input_type` can point to a Pydantic model/dataclass to validate handoff args.

## Adding tools
1) Implement a function tool with `@function_tool` (can accept `RunContextWrapper` as first arg).
2) Register it in `app/utils/tools/registry.py::initialize_tools()` with a stable name.
3) Reference the name in `tool_keys` of any agent spec.

## Runtime knobs (per request)
- `AgentChatRequest.run_options` maps to `RunOptions` → `agents.Runner`:
  - `max_turns`, `previous_response_id`
  - `run_config` keys: `model`, `model_settings`, `input_guardrails`, `output_guardrails`, `tracing_disabled`, `trace_include_sensitive_data`, `workflow_name`
  - `handoff_input_filter` (global, name resolved via `_shared/handoff_filters`)
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

