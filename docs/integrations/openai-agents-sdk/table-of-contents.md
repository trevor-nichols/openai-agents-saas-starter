.
├── agents/                    # Core documentation for the Agents SDK functionality.
│   ├── agents.md              # Documents the main Agent class and its configuration.
│   ├── agents_module.md       # Documents top-level SDK configuration functions (e.g., API keys).
│   ├── exceptions.md          # Documents custom exceptions for the SDK.
│   ├── guardrails.md          # Documents input and output guardrails for safety checks.
│   ├── handoffs.md            # Documents the mechanism for delegating tasks between agents.
│   ├── items.md               # Documents data structures for messages, tool calls, etc. in a run.
│   ├── lifecycle.md           # Documents hooks for observing agent lifecycle events.
│   ├── model_interface.md     # Documents the abstract interfaces for LLM providers and models.
│   ├── model_settings.md      # Documents settings for LLM calls (e.g., temperature).
│   ├── openai_responses_model.md # Documents the model implementation for the OpenAI Responses API.
│   ├── repl.md                # Documents a utility for interactive command-line agent testing.
│   ├── results.md             # Documents the `RunResult` object returned after an agent execution.
│   ├── run_context.md         # Documents the context object passed during an agent run.
│   ├── runner.md              # Documents the `Runner` class used to execute agents.
│   ├── streaming_events.md    # Documents events emitted during a streaming agent run.
│   └── usage.md               # Documents the data structure for tracking token usage.
├── guardrails/                # Documentation for the Guardrails safety feature.
│   ├── agents_sdk_integration.md # Explains how to integrate Guardrails with the Agents SDK.
│   ├── api_reference/         # API reference documentation for the Guardrails SDK.
│   │   ├── exceptions.md      # API reference for custom exceptions used by the Guardrails SDK.
│   │   ├── registry.md        # API reference for the Guardrail specification registry.
│   │   ├── runtime.md         # API reference for runtime helpers that load and execute guardrails.
│   │   ├── spec.md            # API reference for the `GuardrailSpec` class which defines a guardrail.
│   │   └── types.md           # API reference for core data types used in the Guardrails SDK.
│   ├── checks/                # Documentation for specific, pre-built guardrail checks.
│   │   ├── Contains_PII.md    # Documentation for the guardrail that detects Personally Identifiable Information.
│   │   ├── Custom_Prompt_Check.md # Documentation for the guardrail that uses a custom LLM prompt for validation.
│   │   ├── Hallucination_Detection.md # Documentation for the guardrail that detects factual claims unsupported by documents.
│   │   ├── Jailbreak_Detection.md # Documentation for the guardrail that detects attempts to bypass AI safety measures.
│   │   ├── Moderation.md      # Documentation for the guardrail that uses OpenAI's moderation API.
│   │   ├── NSFW_Text.md       # Documentation for the guardrail that detects Not-Safe-For-Work text.
│   │   ├── Off_Topic_Prompts.md # Documentation for the guardrail that ensures content stays within a defined scope.
│   │   ├── Prompt_Injection_Detection.md # Documentation for the guardrail that detects prompt injection in tool calls.
│   │   └── URL_Filter.md      # Documentation for the guardrail that filters URLs against an allow-list.
│   ├── eval_tool.md           # Documentation for a command-line tool to evaluate guardrail performance.
│   ├── streaming_vs_blocking.md # Compares streaming vs. non-streaming guardrail execution modes.
│   └── tripwires.md           # Explains the tripwire mechanism for blocking execution when a guardrail triggers.
├── handoffs/                  # Documentation related to the agent handoff feature.
│   └── handoff_prompt.md      # Provides a recommended system prompt for agents that use handoffs.
├── memory/                    # Documentation for conversation memory and session management.
│   ├── continuing_conversation.md # An example showing how to continue a conversation using `previous_response_id`.
│   ├── examples/              # Contains example scripts for memory features.
│   │   └── session_memmory.md # An example demonstrating session memory for conversation history.
│   ├── long_term_memory_strategies/ # Documentation on strategies for managing long-term conversation memory.
│   │   └── README.md          # Describes strategies like trimming, summarization, and compacting for long-term memory.
│   ├── memory.md              # Documents the base Session protocol and a SQLite implementation.
│   └── sqlalchemy_session.md  # Documents persistent and encrypted session implementations using SQLAlchemy.
├── openai_raw_api_reference.md # Raw API reference for the OpenAI Responses API.
├── output_type/               # Documentation for defining and handling agent output structures.
│   ├── agent_output.md        # Documents schemas and validation for agent outputs.
│   └── structured-output-api.md # A guide to using structured outputs (JSON schema) with the OpenAI API.
├── provider_layer.md          # Architectural overview of the provider layer for model abstraction.
├── streaming/                 # Documentation related to streaming agent responses.
│   └── Streaming_&_Parsing_Reference.md # A comprehensive reference for all streaming events in the SDK.
├── table-of-contents.md       # A table of contents for the entire documentation project.
├── tools/                     # Documentation for all tools available to agents.
│   ├── agents-as-tool/        # Documentation for using one agent as a tool for another.
│   │   └── using-agents-as-tools.md # A guide on how to use one agent as a tool for another agent.
│   ├── code_interpreter/      # Documentation for tools that execute code and shell commands.
│   │   ├── apply-patch.md     # A guide on using the `apply_patch` tool for structured code edits.
│   │   ├── code-interpreter-and-containers.md # A guide to using the Code Interpreter tool and its container environment.
│   │   ├── containers-api.md  # API reference for the Containers endpoint used by Code Interpreter.
│   │   └── shell.md           # A guide on using the `shell` tool to run local commands.
│   ├── conditional-tool-enabling.md # Guide on dynamically enabling or disabling tools at runtime.
│   ├── function_tools/        # Documentation for creating tools from Python functions.
│   │   └── function_schema.md # Documents utilities for creating tool schemas from Python functions.
│   ├── image_generation/      # Documentation for the image generation tool.
│   │   └── image-generation.md # A guide on using the image generation tool within agents.
│   ├── mcp-tools/             # Documentation for the Model Context Protocol (MCP).
│   │   ├── agents-sdk-mcp.md  # A guide on integrating MCP servers with the Agents SDK.
│   │   ├── connectors-&-mcp-servers.md # Explains how to use OpenAI connectors and remote MCP servers.
│   │   ├── mcp-servers.md     # API reference for the various MCPServer classes.
│   │   └── mcp-utils.md       # API reference for MCP utility functions and tool filters.
│   ├── rag/                   # Documentation for Retrieval-Augmented Generation (RAG) tools.
│   │   ├── embeddings.md      # A guide on creating and using vector embeddings.
│   │   ├── file-search.md     # A guide on using the file search tool with vector stores.
│   │   ├── retrieval.md       # A guide on the Retrieval API, semantic search, and vector stores.
│   │   └── vector-stores-&-retrieval-api.md # API reference for Vector Stores and the Retrieval API.
│   ├── raw-outputs/           # Contains raw log files from various streaming tool calls.
│   │   ├── combined-streaming/ # Logs from streaming sessions with multiple tool types.
│   │   │   └── stream-log-2025-11-07T00-28-16.md # A raw log of a streaming session with web search and function calling.
│   │   ├── function-streaming/ # Logs from streaming sessions focused on function tools.
│   │   │   └── stream-log-2025-11-07T00-22-38.md # A raw log of a streaming function calling session.
│   │   └── structured-streaming/ # Logs from streaming sessions with structured (JSON) output.
│   │       ├── stream-log-2025-11-07T17-03-24.md # A raw log of a streaming session producing structured JSON output.
│   │       └── stream-log-2025-11-07T17-32-51.md # Another raw log of a streaming session producing structured JSON output.
│   ├── tool_context.md        # Documents the context object provided during a tool call.
│   ├── tools-overview.md      # An overview of hosted tools, function tools, and agents as tools.
│   ├── tools.md               # API reference for the various tool classes and types.
│   └── web-search/            # Documentation for the web search tool.
│       └── web-search.md      # A guide on using the web search tool and its options.
├── tracing/                   # API documentation for observability and tracing features.
│   ├── create_traces_spans.md # Documents functions for creating traces and spans manually.
│   ├── processor_interface.md # Documents the abstract interfaces for trace processors and exporters.
│   ├── processors.md          # Documents implementations of trace processors (e.g., batch exporter).
│   ├── scope.md               # Documents the scope manager for the current trace/span context.
│   ├── setup.md               # Documents functions for global tracing configuration.
│   ├── span_data.md           # Documents data structures for different types of spans.
│   ├── spans.md               # Documents the base `Span` class for tracing operations.
│   ├── traces.md              # Documents the base `Trace` class for tracing entire workflows.
│   ├── tracing_module.md      # A comprehensive overview of the tracing module's components.
│   └── util.md                # Documents utility functions for tracing (e.g., ID generation).
├── usage/                     # Documentation related to token usage tracking.
│   └── token_usage.md         # Detailed explanation of the token `usage` object in API responses.
└── workflows.md               # Describes how to orchestrate multiple agents in a deterministic sequence.