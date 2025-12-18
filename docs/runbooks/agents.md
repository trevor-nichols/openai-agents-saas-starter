# Agents Runbook

This runbook documents how to add, configure, and test agents and tools in the
API service. The system uses declarative `AgentSpec` files plus centralized tool
registration; the OpenAI Agents SDK runtime is unchanged.

## Concepts
- **AgentSpec** (`app/agents/_shared/specs.py`): declarative metadata for one
  agent (key, display_name, description, model_key, capabilities, prompt
  source, handoff targets, default flag, tool_keys, optional handoff_context).
- **Prompt source**: either inline `instructions` or an external `prompt.md.j2`
  (`prompt_path`). Use `prompt.md.j2` for any non-trivial prompt.
- **Capabilities**: tuples of strings used for catalog/display only; tool
  selection is explicit via `tool_keys`.
- **Handoffs**: `handoff_keys` names of other agents this agent can delegate to.
  Per-handoff state control: set `handoff_context={"target_key": "full"|"fresh"|"last_turn"}`
  to choose how much history the target sees (default `full`).
- **ToolRegistry**: single place tools are registered by name. No automatic
  inclusion or capability filtering—agents list the tools they need via
  `tool_keys`.

## Structured outputs (JSON schema)
- Configure per-agent via `AgentSpec.output: OutputSpec`.
- Fields:
  - `mode`: `"text"` (default) or `"json_schema"`.
  - `type_path`: dotted import path to a Pydantic model or dataclass for the schema.
  - `strict`: `True` (default) requests Structured Outputs (schema-enforced JSON). `False` requests non-strict schema (best-effort JSON).
  - `custom_schema_path`: dotted path to an `AgentOutputSchemaBase` subclass for bespoke validation; takes precedence over `type_path`.
- Example:
  ```python
  from app.agents._shared.specs import AgentSpec, OutputSpec

  AgentSpec(
      key="code_assistant",
      display_name="Code Assistant",
      description="Handles software engineering questions and code reviews.",
      prompt_path=base_dir / "prompt.md.j2",
      tool_keys=("web_search",),
      output=OutputSpec(
          mode="json_schema",
          type_path="app.agents.schemas.code_assistant:AssistantResponse",
          strict=True,   # set False for non-strict JSON
      ),
  )
  ```
- Runtime behavior:
  - The OpenAI registry injects `Agent.output_type` as an `AgentOutputSchema` (or your custom schema).
  - Responses include `structured_output` (parsed object) plus `response` (stringified JSON or text).
  - Conversation history stores the string form; structured payload is preserved on the API response and can be echoed in metadata if needed.
  - Streaming: a terminal SSE event carries `structured_output` and `response_text`; interim deltas stay unchanged.

## Adding a new agent
1) Create a folder `api-service/src/app/agents/<agent_key>/`.
2) Add `spec.py` with `get_agent_spec()` returning `AgentSpec`. Required:
   - `key`, `display_name`, `description`
   - prompt: `prompt_path=base_dir/"prompt.md.j2"` (preferred) or `instructions`
   - `capabilities`: tuple of strings (informational/catalog)
   - `tool_keys`: ordered tuple of tool names to attach (must be registered)
   - optional: `model_key` (maps to `settings.agent_<model_key>_model`),
     `handoff_keys`, `default`, `wrap_with_handoff_prompt`
3) Add `prompt.md.j2` with the system prompt (templated Markdown/Jinja).
4) (Optional) Register any new tools and add their names to `tool_keys`. Agent
   discovery is automatic—no central switchboard edits.

## Tool registration & assignment
- Register tools once in `app/utils/tools/registry.py::initialize_tools()` with
  a stable name (taken from SDK `.name` or the function `__name__`). Category/
  metadata are informational only.
- Attach tools explicitly per agent via `AgentSpec.tool_keys`. Order is
  preserved.
- Missing required tools fail fast during agent build. Optional tools (currently
  only `web_search`, gated by `OPENAI_API_KEY`) log a warning and are skipped.
- Env gating: guard registration in `initialize_tools()` when a provider key is
  absent; agents keep running but will lack that optional tool.

## Handoffs
- Declare handoffs in the orchestrating agent’s `AgentSpec.handoff_keys`.
- The loader builds agents in topological order and will error on cycles or
  missing targets.
- `wrap_with_handoff_prompt=True` will prepend the SDK handoff guidance to the
  prompt (useful for orchestrators like `triage`).
- `handoff_context` controls how much history is forwarded (`full`, `fresh`, `last_turn`).
- `handoff_overrides` let you fine-tune each transfer:
  - `tool_name` / `tool_description`
  - `input_filter` (keyed to `app/agents/_shared/handoff_filters.py`)
  - `input_type` (dotted path to a Pydantic model for validation)
  - `is_enabled` (bool toggle)

## Models
- `model_key` selects the override in settings: `agent_<model_key>_model`.
  Fallback is `agent_default_model`.

## Dynamic prompts (templated Markdown)
- Prompts live in `.md.j2` files so editors highlight both Markdown and Jinja placeholders.
- Use placeholders like `{{ user.name }}` or `{{ run.conversation_id }}`.
- Rendering uses `StrictUndefined` at runtime (missing vars will error), and a permissive mode at boot.

### Runtime context & providers
- Base context available to templates (when data exists):
  - `user.id`
  - `tenant.id`
  - `agent.key`, `agent.display_name`
  - `run.conversation_id`, `run.request_message`
  - `env.environment`
  - `memory.summary`
- Each `AgentSpec` can declare:
  - `prompt_defaults`: seed values for missing fields.
  - `extra_context_providers`: tuple of provider names to enrich context.
- Register custom providers in `app/agents/_shared/prompt_context.py` via:
  ```python
  from app.agents._shared.prompt_context import register_context_provider, PromptRuntimeContext

  @register_context_provider("calendar")
  def calendar_provider(ctx: PromptRuntimeContext, spec):
      return {"next_meeting": "2025-11-25T10:00Z"}
  ```
  Then opt-in per agent with `extra_context_providers=("calendar",)` and use `{{ calendar.next_meeting }}` in the prompt.

### Rendering flow
- AgentService builds a `PromptRuntimeContext` (actor, conversation_id, request_message, settings) and passes it through to the provider runtime.
- The OpenAI registry renders the prompt at request time with that context; handoff wrapping is applied after rendering.
- Chat API accepts `run_options` to pass through SDK controls:
  - `previous_response_id`, `max_turns`
  - `handoff_input_filter` (global)
  - `run_config` (SDK `RunConfig` fields: guardrails, tracing, model overrides)
- Lifecycle hooks are bridged to SSE via `kind="lifecycle"` stream events (agent/tool/LLM start/end, handoff).

## Testing checklist
- `hatch run lint`
- `hatch run typecheck`
- (Optional) add/extend unit tests under `api-service/tests/unit/`:
  - Loader test: specs load without cycles, default agent resolves.
  - Agent-specific smoke: prompt loads, capabilities are as expected.

## Troubleshooting
- **Cycle detected in agent handoffs**: check `handoff_keys` for loops.
- **Missing handoff target**: ensure the target agent directory/key exists.
- **Tool not attached**: ensure the tool is registered in `initialize_tools()`
  and its name appears in the agent’s `tool_keys`; if optional (e.g.,
  `web_search`), verify the required env vars are set.
- **Wrong model**: set the appropriate `AGENT_MODEL_<KEY>` env var (e.g.,
  `AGENT_MODEL_CODE`).
