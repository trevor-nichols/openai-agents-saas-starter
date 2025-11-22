# Provider Layer in api-service

Status: Active (Nov 19, 2025)

## Purpose

Encapsulate all model-provider specifics behind a narrow set of domain ports so the FastAPI services stay provider-neutral. The first concrete implementation is OpenAI.

## Key locations

- **Domain ports:** `api-service/app/domain/ai/ports.py` define `AgentRuntime`, `AgentSessionStore`, `AgentStreamingHandle`, and `AgentProvider`.
- **Domain models:** `api-service/app/domain/ai/models.py` normalize agent descriptors, run results, usage, and stream events.
- **Provider registry:** `api-service/app/services/agents/provider_registry.py` holds registered providers and exposes `get_default()`.
- **OpenAI provider:** `api-service/app/infrastructure/providers/openai/` contains:
  - `provider.py` — assembles the provider, wiring registry + runtime + session store.
  - `registry.py` — builds agent catalog, handoffs, and tool wiring using `ToolRegistry`.
  - `runtime.py` — wraps `agents.Runner` for sync/streaming runs, normalizes usage/events.
  - `session_store.py` — SQLAlchemy-backed SDK sessions (tables `sdk_agent_sessions`, `sdk_agent_session_messages`).
  - `conversation_client.py` — creates OpenAI Conversations (`conv_*`) so the SDK can persist conversation state in the provider’s store.

## Bootstrap flow

FastAPI startup (`api-service/main.py`) now:
1) Initializes the async engine and repositories.
2) Builds the OpenAI provider with the shared engine and conversation search callback.
3) Registers the provider in the registry and sets it as default.
4) Constructs `AgentService` with the registry rather than a concrete SDK.

### Conversation ownership (UUID vs `conv_*`)

- External/UI ID: our UUID (`conversation_id`) continues to identify threads in APIs, URLs, and Postgres (`agent_conversations` / `agent_messages`).
- Provider ID: on first turn we call `OpenAIConversationFactory` to create a provider Conversation and store its `conv_*` in `provider_conversation_id`. The SDK receives that value as `conversation_id` so OpenAI-hosted state is authoritative for cross-turn context.
- Session store: we key `SQLAlchemySession` with the same `conv_*` when available; otherwise we fall back to the local UUID for compatibility.
- Guards: if a stored or returned provider ID is not `conv_*`, we ignore it and proceed without sending it to the provider.

## Adding a new OpenAI surface (future)

1. Create a folder under `app/infrastructure/providers/openai/<surface>/` (e.g., `realtime/`, `guardrails/`).
2. Implement the relevant domain port(s) and keep translation logic local to that folder.
3. Expose the surface via `provider.py` (e.g., attach a new runtime or factory) without changing `AgentService`.

## Adding another provider (e.g., Anthropic)

1. Create `app/infrastructure/providers/anthropic/` with analogous files (`provider.py`, `registry.py`, `runtime.py`, `session_store.py` or equivalent persistence).
2. Register it in bootstrap (`main.py`) via `get_provider_registry().register(...)`; optionally set as default or hold for future tenant overrides.
3. Ensure implementations only touch domain ports; no FastAPI/service imports inside infra.

## Configuration & env vars

- No new env vars were introduced for this milestone. Existing AI settings (`agent_default_model`, `agent_triage_model`, `agent_code_model`, `agent_data_model`, provider API keys) continue to flow through `Settings`.
- Session tables remain `sdk_agent_sessions` / `sdk_agent_session_messages`; table names live in the OpenAI session store constants if customization is ever needed.

## Testing guidance

- Unit/contract tests should register a provider via the registry. The shared pytest fixture in `api-service/tests/conftest.py` demonstrates how to build the OpenAI provider against an in-memory SQLite engine (`reset_provider_registry()` + `build_openai_provider(...)`).
- To stub runtime behavior, patch methods on the provider runtime (`OpenAIAgentRuntime.run` / `run_stream`) instead of touching `agents.Runner` globally.

## Operational notes

- Observability: tracing wraps `AgentService` execution via `agents.trace`; provider runtimes should emit provider-specific metadata in `AgentRunResult.metadata` for metrics/alerts.
- CLI: No CLI changes were required; if future providers add env keys, update `starter_cli/README.md` and the provisioning flows before shipping.
