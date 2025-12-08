# Guardrails package

Operational notes for the guardrails subsystem used by agent specs and tools.

## What lives here
- `_shared/` — core plumbing: `builder` (builds SDK guardrails from configs), `registry` (stores specs/presets), `config_adapter` (bundle resolution), `loaders` (init on startup), `events` (emission helpers), `specs` (config dataclasses).
- `checks/` — individual guardrail checks and their specs (moderation, jailbreak, PII, hallucination, prompt injection, URL filter, etc).
- `presets/` — preset bundles (e.g., `standard`, `strict`, `tool_standard`, `tool_strict`, `minimal`) that group checks for reuse.

## How agents opt in
- In an `AgentSpec`, set `guardrails` to a preset key or explicit config; during agent build the `GuardrailBuilder` attaches input/output guardrails to the SDK `Agent`.
- Tool-level guardrails: `tool_guardrails` applies to all tools; `tool_guardrail_overrides` can disable/replace per tool.
- Runtime behavior: `guardrails_runtime` controls tripwire suppression, streaming vs blocking, concurrency, and result handlers (passed through to the SDK runtime).
- Default guardrails: when `build_openai_provider` is called with guardrails enabled, bundle configs are loaded via `resolve_guardrail_configs` and supplied as defaults for agents/tools that omit explicit configs.

## Lifecycle & events
- Guardrails are initialized at provider bootstrap (`build_openai_provider`) if `enable_guardrails` is True; bundles can be loaded via `guardrail_pipeline_source`.
- Emissions surface as `AgentStreamEvent` items (streaming) and can be collected via `GuardrailEmissionToken`; see `streaming_vs_blocking.md` for behavior differences.

## Adding or tweaking guardrails
- New check: add under `checks/<name>/` with `check.py` and `spec.py`, register in the registry, and include it in relevant presets.
- New preset: add to `presets/` and export from `presets/__init__.py`; update docs if exposed to operators.
- Update bundle/pipeline configs in `docs/integrations/openai-agents-sdk/guardrails/` when changing available checks or presets.

## References
- Agent spec fields: `app/agents/_shared/specs.py` (guardrails*, tool_guardrails*, guardrails_runtime).
- Provider wiring: `app/infrastructure/providers/openai/provider.py` and `registry/agent_builder.py`.
- SDK docs: `docs/integrations/openai-agents-sdk/guardrails/` (tripwires, streaming vs blocking, eval tool, integration).
