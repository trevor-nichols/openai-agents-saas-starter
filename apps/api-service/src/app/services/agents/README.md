# Agents services (orchestration layer)

Glue layer that wires AgentSpecs to runtime execution, sessions, storage, and telemetry.

## What lives here
- `service.py` — façade for chat/chat_stream over the default provider; delegates orchestration to focused run helpers.
- `chat_run.py` — non-streaming chat run orchestration.
- `chat_stream.py` — streaming chat run orchestration.
- `run_finalize.py` — post-run finalization (session sync, usage, event projection, container context).
- `user_input.py` — input attachment resolution + SDK input shaping.
- `asset_linker.py` — best-effort linkage of stored assets to persisted messages.
- `factory.py` — service construction + container wiring helpers.
- `interaction_context.py` — builds `PromptRuntimeContext` (vector stores, container bindings, user/location, env), resolves file_search vector_store_ids, and prepares run metadata.
- `session_manager.py` — resolves provider conversation IDs, wraps SDK sessions with memory strategies (trim/summarize/compact), persists summaries, and syncs session state.
- `run_pipeline.py` — shared pre/post run helpers (record user msg, project session items, memory injection, compaction events).
- `run_options.py` — maps API run options → SDK `RunOptions`.
- `provider_registry.py` — registry for provider instances (OpenAI provider is the default).
- `attachments.py`, `image_ingestor.py` — handle tool/response attachments (images, etc.).
- `catalog.py` — exposes agent descriptors for listing.
- `usage.py`, `event_log.py`, `history.py`, `query.py` — usage accounting and read-only conversation queries.

## How it relates to AgentSpec
- Agent specs stay in `app/agents/**` and define prompts/tools/guardrails/memory defaults. This services layer *consumes* specs via the provider/registry; it does not extend spec fields.
- Vector stores for `file_search` are resolved here (request override → agent binding → spec binding mode). See `interaction_context.py` and the vector_stores README.
- Memory strategies resolved here: request > conversation defaults > agent defaults; applied per session via `StrategySession` in `session_manager.py`.
- Guardrails/tool guardrails are already built into the SDK Agent via the registry; this layer just executes the runtime and forwards guardrail events.

## Run flow (chat/chat_stream)
1) `AgentService` delegates to `ChatRunOrchestrator` / `ChatStreamOrchestrator`, which call `prepare_run_context` (provider, agent descriptor, session, runtime context, memory strategy, conversation defaults).
2) Records the user message, then invokes provider runtime (`OpenAIAgentRuntime`) with resolved run options.
3) Persists assistant message/attachments, projects session items into the event log, syncs session state, and records usage (via `RunFinalizer`).
4) Streaming path also emits lifecycle/memory compaction/guardrail events via `AgentStreamEvent`.

## When to touch this layer
- Add/adjust orchestration behavior (memory defaults, session handling, telemetry).
- Change how vector store bindings or container bindings are resolved before runtime calls.
- Extend usage/event projection or conversation metadata handling.

## References
- Specs: `app/agents/_shared/specs.py`, `app/agents/README.md`
- Provider wiring: `app/infrastructure/providers/openai/`
- Vector stores + file_search: `app/services/vector_stores/README.md`
