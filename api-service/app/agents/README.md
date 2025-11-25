# Agents package

Quick guide for working with agents in this service. For the full runbook see
`docs/runbooks/agents.md`.

## Add an agent
- Create `app/agents/<agent_key>/` with `spec.py` returning an `AgentSpec` via
  `get_agent_spec()`.
- Add `prompt.md.j2` for the system prompt (preferred over inline instructions).
- Set `capabilities`, optional `model_key`, `handoff_keys`, `default`, and
  `wrap_with_handoff_prompt` as needed.
- (Optional) Control handoff state per target with `handoff_context` mapping
  (`full` | `fresh` | `last_turn`); defaults to `full` when unset.
- For dynamic prompts, use Jinja-style placeholders (e.g., `{{ user.id }}`) and
  declare any extra providers in `extra_context_providers`.

## Tools
- Register tools in `app/utils/tools/registry.py::initialize_tools()` with
  metadata (`core`, `agents`, `capabilities`). SDK built-ins and custom
  `@function_tool`s are both registered here.

## Handoffs
- Use `handoff_keys` in the orchestrator’s spec; loader validates missing/cyclic
  dependencies.

## Tests
- `hatch run lint`
- `hatch run typecheck`

Refer to the runbook for details, patterns, and troubleshooting.
