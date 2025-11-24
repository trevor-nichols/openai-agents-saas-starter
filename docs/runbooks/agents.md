# Agents Runbook

This runbook documents how to add, configure, and test agents and tools in the
API service. The system uses declarative `AgentSpec` files plus centralized tool
registration; the OpenAI Agents SDK runtime is unchanged.

## Concepts
- **AgentSpec** (`app/agents/_shared/specs.py`): declarative metadata for one
  agent (key, display_name, description, model_key, capabilities, prompt
  source, handoff targets, default flag).
- **Prompt source**: either inline `instructions` or an external `prompt.md.j2`
  (`prompt_path`). Use `prompt.md.j2` for any non-trivial prompt.
- **Capabilities**: tuples of strings used to match tools; replace the old
  `_AGENT_CAPABILITIES` map.
- **Handoffs**: `handoff_keys` names of other agents this agent can delegate to.
- **ToolRegistry**: single place tools are registered and targeted via
  metadata (`core`, `agents`, `capabilities`, `category`).

## Adding a new agent
1) Create a folder `api-service/app/agents/<agent_key>/`.
2) Add `spec.py` with `get_agent_spec()` returning `AgentSpec`. Required:
   - `key`, `display_name`, `description`
   - prompt: `prompt_path=base_dir/"prompt.md.j2"` (preferred) or `instructions`
   - `capabilities`: tuple of strings (used for tool selection)
   - optional: `model_key` (maps to `settings.agent_<model_key>_model`),
     `handoff_keys`, `default`, `wrap_with_handoff_prompt`
3) Add `prompt.md.j2` with the system prompt (templated Markdown/Jinja).
4) (Optional) Update tools targeting if needed (see below). Discovery is
   automatic—no central switchboard edits.

## Tool registration & targeting
- Tools are registered in `app/utils/tools/registry.py::initialize_tools()`.
- Provide metadata:
  - `core=True` -> all agents get it.
  - `agents=["agent_key", ...]` -> explicit targeting.
  - `capabilities=["foo", ...]` -> any agent with that capability gets it.
  - `category` and `description` are for cataloging/observability.
- OpenAI SDK built-ins (e.g., `CodeInterpreterTool`) and custom `@function_tool`
  are treated the same: instantiate, register with metadata.
- Env gating: if a tool needs an API key/flag, guard its registration in
  `initialize_tools()` (see Tavily example).

## Handoffs
- Declare handoffs in the orchestrating agent’s `AgentSpec.handoff_keys`.
- The loader builds agents in topological order and will error on cycles or
  missing targets.
- `wrap_with_handoff_prompt=True` will prepend the SDK handoff guidance to the
  prompt (useful for orchestrators like `triage`).

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
- Each `AgentSpec` can declare:
  - `prompt_context_keys`: expected top-level keys (helps readability; validation uses StrictUndefined).
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

## Testing checklist
- `hatch run lint`
- `hatch run typecheck`
- (Optional) add/extend unit tests under `api-service/tests/unit/`:
  - Loader test: specs load without cycles, default agent resolves.
  - Agent-specific smoke: prompt loads, capabilities are as expected.

## Troubleshooting
- **Cycle detected in agent handoffs**: check `handoff_keys` for loops.
- **Missing handoff target**: ensure the target agent directory/key exists.
- **Tool not attached**: confirm metadata (`agents`/`capabilities`) and that the
  tool isn’t gated by missing env vars.
- **Wrong model**: set the appropriate `AGENT_MODEL_<KEY>` env var (e.g.,
  `AGENT_MODEL_CODE`).
