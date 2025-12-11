# Guardrails System Implementation

_Last updated: 2025-12-08 (post-completion maintenance note)_
**Status:** ✅ Complete
**Owner:** Platform Engineering
**Domain:** Backend | Cross-cutting
**ID / Links:** [OpenAI Agents SDK Guardrails Docs](../../../docs/integrations/openai-agents-sdk/guardrails/)

---

## Recent Updates

- Split PII guardrails into stage-specific specs: `pii_detection_input` (pre-flight/input) and `pii_detection_output` (output), with presets updated accordingly.
- Guardrail builder now rejects `tool_input`/`tool_output` stages for agent guardrails; tool-level guardrails to be attached via tool builders when implemented.
- Guardrail output normalization sets `guardrail_name` from the spec display name when missing to keep outputs consistent across stages.
- Documented guardrail stage coverage vs. OpenAI stages and captured the remaining gap (tool-level guardrails).
- Added tool-level guardrails (tool_input/tool_output) for PII and prompt injection, with prefixed presets (`tool_standard`, `tool_strict`) and ToolResolver/GuardrailBuilder wiring plus unit tests.

---

## Coverage vs. OpenAI Guardrail Stages

- OpenAI stages: `pre_flight`, `input`, `output`, `tool_input`, `tool_output`.
- Implemented (agent-level):
  - Input/pre-flight: `pii_detection_input`, `moderation`, `jailbreak_detection`, `custom_prompt`.
  - Output: `pii_detection_output`, `prompt_injection`, `hallucination`, `url_filter`.
- Implemented (tool-level, initial set): `pii_tool_input`, `pii_tool_output`, `prompt_injection_tool_input`, `prompt_injection_tool_output` with presets (`tool_standard`, `tool_strict`).
- Remaining (tool-level, future): Extend tool-level coverage to other checks (e.g., moderation, URL filter) as needed.

---

## Objective

Implement a comprehensive, declarative guardrails system that integrates with the OpenAI Agents SDK, enabling agents to enforce safety policies (PII detection, jailbreak prevention, hallucination detection, etc.) through a clean, registry-based architecture that mirrors existing patterns for tools and agents.

---

## Definition of Done

- [x] `GuardrailSpec` and related dataclasses implemented in `app/guardrails/_shared/specs.py`
- [x] `GuardrailRegistry` implemented with spec and preset registration
- [x] `GuardrailBuilder` constructs SDK-compatible guardrail functions from specs
- [x] Individual guardrail checks implemented (PII, Jailbreak, Moderation, Prompt Injection, Hallucination, URL Filter, Custom Prompt)
- [x] Guardrail presets defined (standard, strict, minimal)
- [x] `AgentSpec` extended with `guardrails` configuration field
- [x] `AgentBuilder` wires guardrails when constructing agents
- [x] API endpoints for guardrail catalog (`/api/v1/guardrails`)
- [x] Unit tests for all guardrail components (46 tests passing)
- [x] `hatch run lint` passes
- [x] `hatch run typecheck` passes
- [x] Docs/trackers updated

---

## Scope

### In Scope

- Core guardrail specification types (`GuardrailSpec`, `GuardrailCheckResult`, `GuardrailPreset`, etc.)
- Guardrail registry for centralized management
- Guardrail builder for SDK integration
- Individual guardrail check implementations:
  - PII Detection (using Presidio patterns)
  - Jailbreak Detection (LLM-based)
  - Moderation (OpenAI moderation API)
  - Prompt Injection Detection (LLM-based)
  - Hallucination Detection (LLM + vector store)
  - URL Filter (regex-based)
  - Custom Prompt Check (LLM-based)
- Guardrail presets for common configurations
- Agent spec extension for guardrail configuration
- API endpoints for guardrail catalog

### Out of Scope

- Frontend UI for guardrail configuration (future milestone)
- Guardrail analytics/dashboards (future milestone)
- Custom guardrail authoring UI (future milestone)
- External guardrail provider integrations (future milestone)

---

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Design approved, follows existing patterns |
| Implementation | ✅ | All components implemented |
| Tests & QA | ✅ | 46 unit tests passing |
| Docs & runbooks | ✅ | This tracker updated |

---

## Architecture / Design Snapshot

### Key Decisions

1. **Registry Pattern**: Mirror existing `ToolRegistry` and `OpenAIAgentRegistry` patterns
2. **Declarative Specs**: Use frozen dataclasses like `AgentSpec` and `WorkflowSpec`
3. **Builder Pattern**: `GuardrailBuilder` constructs SDK guardrails from specs
4. **Preset Composition**: Allow presets to compose guardrails, agents to compose presets
5. **Dotted Path Imports**: Check functions referenced by dotted path (like handoff filters)

### New Modules

```
app/guardrails/
├── __init__.py
├── _shared/
│   ├── __init__.py
│   ├── specs.py          # GuardrailSpec, GuardrailCheckResult, etc.
│   ├── registry.py       # GuardrailRegistry
│   ├── loaders.py        # load_guardrail_specs(), load_guardrail_presets()
│   └── builder.py        # GuardrailBuilder
├── checks/
│   ├── __init__.py
│   ├── pii_detection/
│   ├── jailbreak_detection/
│   ├── prompt_injection/
│   ├── hallucination/
│   ├── moderation/
│   ├── url_filter/
│   └── custom_prompt/
└── presets/
    ├── __init__.py
    ├── standard.py
    ├── strict.py
    └── minimal.py
```

### Integration Points

- `AgentSpec`: Add `guardrails: AgentGuardrailConfig | None` field
- `AgentBuilder.build_agent()`: Wire `input_guardrails` and `output_guardrails`
- `OpenAIAgentRegistry`: Initialize `GuardrailRegistry` and `GuardrailBuilder`
- `build_openai_provider()`: Auto-initialize guardrails when enabled

---

## Workstreams & Tasks

### Workstream A – Core Infrastructure

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Specs | Create `GuardrailSpec`, `GuardrailCheckResult`, `GuardrailPreset` dataclasses | ✅ |
| A2 | Registry | Implement `GuardrailRegistry` with spec/preset management | ✅ |
| A3 | Loaders | Implement `load_guardrail_specs()` and `load_guardrail_presets()` | ✅ |
| A4 | Builder | Implement `GuardrailBuilder` for SDK integration | ✅ |

### Workstream B – Guardrail Checks

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | PII | Implement PII detection check (regex-based, Presidio patterns) | ✅ |
| B2 | Jailbreak | Implement jailbreak detection check (LLM-based) | ✅ |
| B3 | Moderation | Implement moderation check (OpenAI API) | ✅ |
| B4 | Injection | Implement prompt injection detection (LLM-based) | ✅ |
| B5 | Hallucination | Implement hallucination detection (LLM + vector store) | ✅ |
| B6 | URL | Implement URL filter check (regex allow/block lists) | ✅ |
| B7 | Custom | Implement custom prompt check (LLM-based) | ✅ |

### Workstream C – Presets & Integration

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Presets | Define standard, strict, minimal presets | ✅ |
| C2 | AgentSpec | Extend `AgentSpec` with guardrails config | ✅ |
| C3 | Builder | Integrate `GuardrailBuilder` into `AgentBuilder` | ✅ |
| C4 | API | Add `/api/v1/guardrails` endpoints | ✅ |

### Workstream E – Tool-Level Guardrails (Backlog)

| ID | Area | Description | Status |
|----|------|-------------|--------|
| E1 | Tool stages | Design and implement tool-level guardrail builder/attachments for `tool_input` / `tool_output` stages | ✅ |
| E2 | Specs | Add tool-scoped guardrail specs/presets (initial set: PII + prompt injection) | ✅ |
| E3 | Tests | Unit coverage for tool guardrails and presets | ✅ |

### Workstream D – Testing & QA

| ID | Area | Description | Status |
|----|------|-------------|--------|
| D1 | Unit | Unit tests for specs and registry | ✅ |
| D2 | Unit | Unit tests for builder | ✅ |
| D3 | Unit | Unit tests for loaders | ✅ |
| D4 | Lint | Run `hatch run lint` | ✅ |
| D5 | Types | Run `hatch run typecheck` | ✅ |

---

## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Design | Architecture approval | Design documented, patterns identified | ✅ | 2025-12-07 |
| P1 – Core | Specs, Registry, Builder | Core infrastructure working | ✅ | 2025-12-08 |
| P2 – Checks | Individual guardrail checks | All 7 checks implemented | ✅ | 2025-12-08 |
| P3 – Integration | AgentSpec, API, Presets | Full integration working | ✅ | 2025-12-08 |
| P4 – QA | Tests, Lint, Types | All checks pass | ✅ | 2025-12-08 |

---

## Dependencies

- OpenAI Agents SDK (v0.6.1+) - for `InputGuardrail`, `OutputGuardrail` types
- OpenAI API - for moderation endpoint, LLM-based checks
- Existing `AgentSpec`, `AgentBuilder`, `ToolRegistry` patterns

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| SDK guardrail API changes | Medium | Pin SDK version, monitor releases |
| LLM-based checks add latency | Medium | Make checks configurable, async execution |
| Complex check logic | Low | Follow existing patterns, comprehensive tests |

---

## Validation / QA Plan

- `hatch run lint` - Ruff linting ✅
- `hatch run typecheck` - Pyright + Mypy type checking ✅
- `pytest tests/unit/guardrails/` - Unit tests for guardrails (46 tests) ✅
- Manual verification: Create agent with guardrails, verify tripwire behavior

---

## Rollout / Ops Notes

- Guardrails are opt-in via `AgentSpec.guardrails` field
- Existing agents unaffected (no guardrails by default)
- Presets provide quick enablement without per-guardrail config
- No migrations required (pure additive change)
- Guardrails auto-initialized when `build_openai_provider()` is called with `enable_guardrails=True` (default)

---

## Usage Example

```python
from app.agents._shared.specs import AgentSpec
from app.guardrails._shared.specs import AgentGuardrailConfig, GuardrailCheckConfig

# Use a preset for quick configuration
agent_spec = AgentSpec(
    key="safe_assistant",
    display_name="Safe Assistant",
    description="An assistant with safety guardrails",
    guardrails=AgentGuardrailConfig(preset="standard"),
    # ... other agent config
)

# Or configure specific guardrails
agent_spec = AgentSpec(
    key="custom_assistant",
    display_name="Custom Assistant",
    description="An assistant with custom guardrails",
    guardrails=AgentGuardrailConfig(
        guardrail_keys=("pii_detection_input", "pii_detection_output", "moderation"),
        guardrails=(
            GuardrailCheckConfig(
                guardrail_key="pii_detection_input",
                config={"block": True, "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"]},
            ),
        ),
    ),
    # ... other agent config
)
```

---

## Changelog

- 2025-12-07 — Initial milestone created, design approved
- 2025-12-07 — Starting implementation of core infrastructure
- 2025-12-08 — Implementation complete:
  - Core specs and types (`GuardrailSpec`, `GuardrailCheckResult`, etc.)
  - Registry with spec/preset management
  - Builder for SDK integration
  - All 7 guardrail checks (PII, Jailbreak, Moderation, Prompt Injection, Hallucination, URL Filter, Custom Prompt)
  - 3 presets (standard, strict, minimal)
  - AgentSpec extension with guardrails field
  - AgentBuilder integration
  - API endpoints (`/api/v1/guardrails`)
  - 46 unit tests passing
  - Lint and type checks passing
- 2025-12-08 — Tool-level guardrails added (PII + prompt injection for tool_input/tool_output), prefixed tool presets (`tool_standard`, `tool_strict`), builder/resolver wiring, and unit tests.
