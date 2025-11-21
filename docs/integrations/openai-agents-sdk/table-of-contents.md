.
├── agents/                    # Core documentation for the Agents SDK functionality.
│   ├── agent_output.md        # Documents schemas and validation for agent outputs.
│   ├── agents.md              # Documents the main Agent class and its configuration.
│   ├── agents_module.md       # Documents top-level SDK configuration functions (e.g., API keys).
│   ├── exceptions.md          # Documents custom exceptions for the SDK.
│   ├── function_schema.md     # Documents utilities for creating tool schemas from Python functions.
│   ├── guardrails.md          # Documents input and output guardrails for safety checks.
│   ├── handoffs.md            # Documents the mechanism for delegating tasks between agents.
│   ├── items.md               # Documents data structures for messages, tool calls, etc. in a run.
│   ├── lifecycle.md           # Documents hooks for observing agent lifecycle events.
│   ├── mcp_servers.md         # Documents classes for Model Context Protocol (MCP) servers.
│   ├── mcp_util.md            # Documents utilities for working with MCP tools and servers.
│   ├── memory.md              # Documents the base Session protocol for conversation history.
│   ├── model_interface.md     # Documents the abstract interfaces for LLM providers and models.
│   ├── model_settings.md      # Documents settings for LLM calls (e.g., temperature).
│   ├── openai_chat_completions.md # Documents the model implementation for the OpenAI Chat Completions API.
│   ├── openai_responses_model.md # Documents the model implementation for the OpenAI Responses API.
│   ├── repl.md                # Documents a utility for interactive command-line agent testing.
│   ├── results.md             # Documents the `RunResult` object returned after an agent execution.
│   ├── run_context.md         # Documents the context object passed during an agent run.
│   ├── runner.md              # Documents the `Runner` class used to execute agents.
│   ├── streaming_events.md    # Documents events emitted during a streaming agent run.
│   ├── tool_context.md        # Documents the context object provided during a tool call.
│   ├── tools.md               # Documents the various types of tools agents can use.
│   └── usage.md               # Documents the data structure for tracking token usage.
├── examples/                  # Contains example code and usage guides.
│   ├── memory/                # Examples related to conversation memory management.
│   │   └── session_memmory.md # An example demonstrating session memory for conversation history.
│   └── tools/                 # Examples related to using tools with agents.
│       └── tools.md           # Guide on using hosted tools, function tools, and agents as tools.
├── handoffs/                  # Documentation related to the agent handoff feature.
│   └── handoff_prompt.md      # Provides a recommended system prompt for agents that use handoffs.
├── provider_layer.md          # How api-service wires provider-agnostic ports and the OpenAI provider.
├── memory/                    # Documentation for specific memory/session implementations.
│   └── sqlalchemy_session.md  # Documents a persistent session implementation using SQLAlchemy.
├── openai_raw_api_reference.md # Raw API reference documentation for the OpenAI Responses API.
└── tracing/                   # API documentation for observability and tracing features.
    ├── create_traces_spans.md # Documents functions for creating traces and spans manually.
    ├── processor_interface.md # Documents the abstract interfaces for trace processors and exporters.
    ├── processors.md          # Documents implementations of trace processors (e.g., batch exporter).
    ├── scope.md               # Documents the scope manager for the current trace/span context.
    ├── setup.md               # Documents functions for global tracing configuration.
    ├── span_data.md           # Documents data structures for different types of spans.
    ├── spans.md               # Documents the base `Span` class for tracing operations.
    ├── traces.md              # Documents the base `Trace` class for tracing entire workflows.
    ├── tracing_module.md      # A comprehensive overview of the tracing module's components.
    └── util.md                # Documents utility functions for tracing (e.g., ID generation).
