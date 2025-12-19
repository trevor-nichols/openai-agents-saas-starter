# Creating AI Agents

This guide explains how to create, configure, and wire up new AI agents in the platform.

The architecture separates the **Agent Definition** (declarative spec) from the **Runtime** (OpenAI/LLM integration). This allows you to define agents using simple Python data structures without worrying about session management, history, or API connection logic.

## 1. Directory Structure

Agents live in `src/app/agents/`. Each agent gets its own directory containing at least two files:

```text
src/app/agents/
├── my_new_agent/           # 1. Create a directory (snake_case)
│   ├── __init__.py         #    (Empty file)
│   ├── spec.py             # 2. The Configuration (AgentSpec)
│   └── prompt.md.j2        # 3. The System Prompt (Jinja2)
```

## 2. Quick Start: "Hello World" Agent

To create a simple agent that acts as the entry point:

**1. Create the prompt (`src/app/agents/simple_bot/prompt.md.j2`)**
```markdown
You are a helpful assistant named {{ agent.display_name }}.
The current user is {{ user.id }}.
Today is {{ date_and_time }}.
```

**2. Create the spec (`src/app/agents/simple_bot/spec.py`)**
```python
from pathlib import Path
from app.agents._shared.specs import AgentSpec

def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        key="simple_bot",
        display_name="Simple Bot",
        description="A basic assistant for testing.",
        # Sets this agent as the starting point for new conversations
        default=True,
        # Tools are referenced by string ID
        tool_keys=("web_search",),
        # Point to the prompt file relative to this script
        prompt_path=Path(__file__).parent / "prompt.md.j2",
    )
```

**3. Restart the API.** The system automatically discovers new agents on startup.

---

## 3. Core Concepts

### Tools vs. Handoffs vs. Sub-Agents
It is crucial to understand the three ways an agent interacts with the world:

| Feature | Description | Code Config |
| :--- | :--- | :--- |
| **Tools** | Functions the agent calls to get data (Search, Code, Database). The agent stays in control. | `tool_keys=("web_search",)` |
| **Handoffs** | The agent transfers control to another agent. **The current agent stops running.** Useful for routing (Triage -> Support). | `handoff_keys=("support_agent",)` |
| **Sub-Agents** | The agent calls another agent *like a tool*. The parent waits for the result, then continues. Useful for delegation (Manager -> Researcher). | `agent_tool_keys=("researcher",)` |

### Context & Memory
When an agent runs, it needs context. You control handoff history via `handoff_context`:
*   **`full`**: The target agent receives the entire conversation history (Default).
*   **`fresh`**: The target agent starts with a blank slate (history is hidden).
*   **`last_turn`**: The target agent sees only the user's most recent message.

### Prompt Context Variables
These variables are automatically available in your `prompt.md.j2` templates when a runtime context exists:

| Key | Description | Example Access |
| :--- | :--- | :--- |
| `user` | The active user | `{{ user.id }}` |
| `tenant` | The active tenant | `{{ tenant.id }}` |
| `env` | Runtime environment info | `{{ env.environment }}` |
| `run` | Current request metadata | `{{ run.conversation_id }}`, `{{ run.request_message }}` |
| `agent` | This agent's identity | `{{ agent.display_name }}`, `{{ agent.key }}` |
| `memory`| Long-term summary (if enabled)| `{{ memory.summary }}` |
| `date` | Current date (UTC, e.g. `December 18, 2025`) | `{{ date }}` |
| `time` | Current time (UTC, e.g. `16:04 UTC`) | `{{ time }}` |
| `date_and_time` | Current date & time (UTC, e.g. `December 18, 2025 at 16:04 UTC`) | `{{ date_and_time }}` |

### Prompt Defaults (Static Context)
You can reuse the same `.md.j2` file across multiple agents by injecting static default variables via `prompt_defaults`. If you reference a custom variable in the prompt, provide it here or via an `extra_context_provider` to avoid template validation errors.
```python
AgentSpec(
    ...,
    prompt_path=Path("generic_persona.md.j2"),
    # Access in Jinja as {{ tone }}
    prompt_defaults={"tone": "pirate", "verbosity": "high"}
)
```

### Custom Context Providers
You can create dynamic context variables by registering a Python function. Provider outputs are injected globally, so keep them lightweight.

1.  **Define the provider** in your code (e.g., `src/app/agents/_shared/prompt_context.py`):
    ```python
    from app.agents._shared.prompt_context import register_context_provider

    @register_context_provider("weather")
    def weather_provider(ctx, spec):
        # Fetch logic here
        return {"current": "Sunny", "temp": 72}
    ```
2.  **Use it** in your prompt: `It is currently {{ weather.current }}`.

---

## 4. Configuration Reference

### Model Resolution (default vs fixed)
There is a single global default model, and agents may optionally fix themselves to a specific model.

- **Global default:** `AGENT_MODEL_DEFAULT` (`agent_default_model`) in `src/app/core/settings/ai.py`.
- **Per-agent fixed model:** set `model="..."` in the agent spec. When set, that agent always uses that model.
- **Settings-selected model:** set `model_key="triage"|"code"|"data"` to opt into a settings/env override bucket.

Resolution order is:
1) `model` from the spec (if set; fixed)
2) `model_key` → `AGENT_MODEL_<KEY>` (if set)
3) `AGENT_MODEL_DEFAULT` (`agent_default_model`)

`model_key` maps to environment variables defined in `src/app/core/settings/ai.py`:
- **Logic:** `model_key="triage"` -> looks for `agent_triage_model` -> env `AGENT_MODEL_TRIAGE`.
- **Fallback:** If the specific key isn't set, it falls back through the order above.

| `model_key` Value | Mapped Env Variable | Default Value |
| :--- | :--- | :--- |
| `None` (Default) | `AGENT_MODEL_DEFAULT` | `gpt-5.1` |
| `"triage"` | `AGENT_MODEL_TRIAGE` | `None` (Falls back to Default) |
| `"code"` | `AGENT_MODEL_CODE` | `None` (Falls back to Default) |
| `"data"` | `AGENT_MODEL_DATA` | `None` (Falls back to Default) |

**Per-agent overrides (recommended for production operations):**
If you need per-agent rollouts without code changes, prefer introducing a new `model_key` bucket in `src/app/core/settings/ai.py` and using it in specs.

### Standard Tools
These keys can be added to `tool_keys`:
*   **`web_search`**: OpenAI hosted web search (requires `OPENAI_API_KEY`).
*   **`file_search`**: RAG (Retrieval Augmented Generation) over vector stores.
*   **`code_interpreter`**: Sandboxed Python execution environment.
*   **`image_generation`**: DALL-E 3 image generation.
*   **`get_current_time`**: Returns current UTC timestamp.
*   **`search_conversations`**: Semantically search past chat history.

### Hosted MCP Tools
You can add tools defined via the **Model Context Protocol** (MCP) without writing Python code. Configure the `MCP_TOOLS` environment variable (JSON), and the tools will automatically appear in the registry. **Note:** hosted MCP tools are only registered when `OPENAI_API_KEY` is set; without it they are skipped.

**1. Configure Env:**
```json
MCP_TOOLS=[{"name": "weather_mcp", "server_label": "Weather", "server_url": "https://mcp.weather.com"}]
```

**2. Add to Spec:**
```python
AgentSpec(
    ...,
    tool_keys=("weather_mcp",) # Name matches the JSON config
)
```

### Tool Configuration (`tool_configs`)
Some tools require specific runtime settings.

**Code Interpreter & Image Generation:**
Pass these inside the `tool_configs` dictionary.
```python
tool_configs={
    "code_interpreter": {
        "mode": "auto",        # "auto" (default) or "explicit"
        "memory_limit": "4g",  # Options: 1g, 4g, 16g, 64g
        "file_ids": [...]      # List of file IDs to pre-load into the sandbox
    },
    "image_generation": {
        "size": "1024x1024",
        "quality": "high",     # "auto", "low", "medium", or "high"
        "output_format": "png",
        "background": "auto",  # "auto", "opaque", or "transparent"
        "partial_images": 2    # 0-3; capped by settings.image_max_partial_images
    }
}
```

**File Search (`file_search_options` & `vector_store_binding`):**
File search behavior is controlled by two top-level arguments.

1. **`vector_store_binding`**: Controls *which* database is queried.

| Mode | Description |
| :--- | :--- |
| `tenant_default` | (Default) Uses the tenant's primary vector store. If one does not exist, the system automatically creates one. |
| `required` | Attempts to use the tenant's primary vector store. Errors if it does not exist (useful if you manage stores strictly via API). |
| `static` | Requires `vector_store_ids` to be explicitly set in the spec. Uses that exact ID regardless of tenant. |

2. **`file_search_options`**: Controls *how* the query runs.
```python
AgentSpec(
    ...,
    tool_keys=("file_search",),
    vector_store_binding="tenant_default",
    file_search_options={
        "max_num_results": 5,
        "include_search_results": True, # Include raw snippets in context
        "ranking_options": {"score_threshold": 0.5},
        # Metadata filtering (matches OpenAI Vector Store filtering syntax)
        "filters": {"category": "technical_docs"} 
    }
)
```

### Guardrails (Safety & Policy)
You can attach safety checks to agents using `AgentGuardrailConfig`.

**Presets:**
*   **`minimal`**: Low latency. Basic regex PII masking and API moderation.
*   **`standard`**: Balanced. Adds jailbreak detection and stricter PII rules.
*   **`strict`**: Enterprise. Blocks PII (no masking) and lowers tolerance thresholds.

```python
from app.agents._shared.specs import (
    AgentGuardrailConfig, 
    ToolGuardrailConfig, 
    GuardrailRuntimeOptions
)

AgentSpec(
    # ...
    # 1. Agent-level Guardrails (Inputs/Outputs)
    guardrails=AgentGuardrailConfig(preset="standard"),
    
    # 2. Tool-level Guardrails (Prevent sensitive data passing to tools)
    tool_guardrails=ToolGuardrailConfig(
        input=AgentGuardrailConfig(preset="tool_standard")
    ),

    # 3. Specific Tool Overrides (Optional)
    tool_guardrail_overrides={
        "code_interpreter": ToolGuardrailConfig(
            input=AgentGuardrailConfig(preset="strict") # Stricter checks for code input
        )
    },

    # 4. Runtime Options (Optional)
    guardrails_runtime=GuardrailRuntimeOptions(
        suppress_tripwire=False, # If True, logs violations but doesn't crash the request
        concurrency=5            # Max concurrent guardrail checks
    )
)
```

### Structured Output
To force the agent to return JSON matching a schema:

```python
from app.agents._shared.specs import OutputSpec

# Option A: Using a Pydantic model (defined in your app code)
output=OutputSpec(
    mode="json_schema",
    type_path="app.api.models.MyResponseModel",
    strict=True # Enables OpenAI Strict Mode
)

# Option B: Using a custom validation class (inheriting from AgentOutputSchemaBase)
output=OutputSpec(
    mode="json_schema",
    custom_schema_path="app.schemas.MyComplexValidator"
)
```

### Memory Management (`memory_strategy`)
Controls how the conversation history is truncated or compressed before being sent to the LLM. Precedence is request overrides > conversation defaults > agent spec defaults.

```python
memory_strategy={
    "mode": "trim",            # "trim", "summarize", or "compact"
    "max_user_turns": 20,      # Keep only the last 20 user exchanges
    "keep_last_user_turns": 2, # Always safeguard the most recent 2 turns
    "token_budget": 40000,     # Max logical tokens allowed in history
}
```

---

## 5. The Agent Spec Reference

The `AgentSpec` dataclass is the single source of truth for an agent.

```python
from dataclasses import dataclass
from pathlib import Path
from app.agents._shared.specs import (
    AgentGuardrailConfig, 
    OutputSpec, 
    HandoffConfig, 
    AgentToolConfig,
    ToolGuardrailConfig, 
    GuardrailRuntimeOptions
)

@dataclass(frozen=True, slots=True)
class AgentSpec:
    # --- Identity ---
    key: str                    # Unique ID (used in API and handoffs)
    display_name: str           # Human-readable name (e.g., "Data Analyst")
    description: str            # Description visible to other agents/tools
    default: bool = False       # If True, this agent handles new conversations by default
    capabilities: tuple = ()    # Tags for UI filtering (e.g., "research", "code")

    # --- Model & Prompt ---
    # Maps to Settings.agent_{model_key}_model. Must exist in settings/ai.py!
    model_key: str | None = None      
    
    prompt_path: Path | None = None   # Path to .md.j2 file
    instructions: str | None = None   # OR raw string instructions
    prompt_defaults: dict = {}        # Static Jinja2 variables (e.g. {"tone": "helpful"})
    wrap_with_handoff_prompt: bool = False # Prepend standard routing instructions

    # --- Capabilities ---
    tool_keys: tuple = ()             # List of tool keys ("web_search", "code_interpreter")
    handoff_keys: tuple = ()          # List of agents this one can transfer to
    agent_tool_keys: tuple = ()       # List of agents callable as tools (Sub-Agents)
    
    # --- Configuration ---
    tool_configs: dict = {}           # Runtime args (e.g. {"image_generation": {"size": "1024x1024"}})
    
    # Fine-grained control over how handoffs are presented to the LLM
    # Keys must match `handoff_keys`
    handoff_overrides: dict[str, HandoffConfig] = {} 
    
    # Fine-grained control over how Sub-Agents appear (e.g. renaming them)
    agent_tool_overrides: dict[str, AgentToolConfig] = {}

    # Control history policy per target (e.g. {"billing": "fresh"})
    handoff_context: dict[str, str] = {}         # Only "full", "fresh", "last_turn" are valid

    # --- Memory Management ---
    # keys: mode="trim"|"compact", max_user_turns=int, token_budget=int
    memory_strategy: dict = None       

    # --- RAG / Vector Store ---
    vector_store_binding: str = "tenant_default" # "tenant_default", "static", "required"
    vector_store_ids: tuple = ()                 # Specific IDs if binding is "static"
    file_search_options: dict = None             # kwargs: max_num_results, ranking_options
    
    # --- Safety & Output ---
    guardrails: AgentGuardrailConfig = None             # Input/Output validation rules
    tool_guardrails: ToolGuardrailConfig = None         # Tool Input/Output validation rules
    tool_guardrail_overrides: dict[str, ToolGuardrailConfig] = {} # Per-tool overrides
    guardrails_runtime: GuardrailRuntimeOptions = None  # Execution options
    output: OutputSpec = None                           # Enforce JSON Schema / Pydantic outputs
```

---

## 6. Common Patterns

### The Router Pattern (Triage)
A "Triage" agent usually sits at the front. It has `fresh` handoffs to specialists and uses no heavy tools itself.

Crucially, set `wrap_with_handoff_prompt=True` so the system automatically injects instructions teaching the model how to use the handoff tools.

```python
AgentSpec(
    key="triage",
    default=True,  # This is the entry point
    # ...
    handoff_keys=("billing", "tech_support"),
    handoff_context={"billing": "full", "tech_support": "full"},
    wrap_with_handoff_prompt=True, # Injects routing instructions automatically
)
```

### The Renamed Sub-Agent
If you have a generic agent (e.g., "Researcher") but want the calling agent to see it as a specific role (e.g., "CompetitorAnalyst").

You can also use a `custom_output_extractor` to control what the parent agent sees. By default, the parent sees the entire sub-chat. You might want to return only the final answer to save tokens.

```python
from app.agents._shared.specs import AgentToolConfig

AgentSpec(
    key="product_manager",
    agent_tool_keys=("researcher",),
    # Rename the tool so the model understands its specific role here
    agent_tool_overrides={
        "researcher": AgentToolConfig(
            tool_name="competitor_analyst",
            tool_description="Looks up competitor pricing data.",
            # Optional: dotted path to a function(AgentRunResult) -> str
            custom_output_extractor="app.utils.extractors.summarize_finding"
        )
    }
)
```

### The Specialist Pattern with Validated Handoffs
Specialists usually have `fresh` context (to avoid noise from previous agents). You can also validate arguments passed during handoff using `input_type`.

```python
from app.agents._shared.specs import HandoffConfig

AgentSpec(
    key="billing",
    model_key="data",
    handoff_keys=("triage",),
    # Ensure the model passes the correct ID when handing off to triage
    handoff_overrides={
        "triage": HandoffConfig(
            tool_name="return_to_main_menu",
            input_type="app.api.models.HandoffReturnArgs" # Pydantic model path
        )
    }
)
```

---

## 7. Troubleshooting

**Agent not showing up in API?**
1. Ensure the directory has an `__init__.py`.
2. Ensure `spec.py` exports a function `get_agent_spec()`.
3. Check logs for "Duplicate agent key" errors if you copy-pasted a folder.

**Template Errors / Startup Crashes?**
The system validates Jinja2 templates on startup. If your `prompt.md.j2` uses a custom variable (e.g. `{{ tone }}`), provide it via `prompt_defaults` or an `extra_context_provider`. Built-in keys (`user`, `tenant`, `agent`, `run`, `env`, `memory`) are injected automatically.

**File Search not working?**
Ensure `vector_store_binding` is set. If set to `tenant_default` (default), the system expects the tenant to have a vector store provisioned. If the store is missing, the system automatically creates one unless configured otherwise. If set to `required`, the operation will fail if the tenant has no store.

**Agent using the wrong model?**
If you set `model_key="my_custom_model"`, verify that `agent_my_custom_model` exists in `src/app/core/settings/ai.py`. If it doesn't exist, the system silently falls back to `agent_default_model`.
