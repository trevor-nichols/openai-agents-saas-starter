# OpenAI Provider (api-service)

Small guide to the OpenAI provider wiring under `app/infrastructure/providers/openai`.

## What lives here
- `provider.py` — assembles the concrete `OpenAIAgentProvider`, wiring registry, runtime, session store, and conversation factory.
- `registry/` — builds agent descriptors, tools, and handoff wiring for the OpenAI surface.
- `runtime.py` — thin wrapper around `agents.Runner` for sync + streaming runs.
- `session_store.py` — SQLAlchemy-backed SDK session store (see below).
- `conversation_client.py` — creates provider Conversations (`conv_*`) that the SDK uses as the authoritative thread ID.
- `context.py`, `run_config.py`, `tool_calls.py`, `usage.py`, `streaming.py`, `lifecycle.py` — helpers that keep provider-specific logic out of domain services.

## Session store + database tables
- We persist OpenAI Agents SDK session history via `OpenAISQLAlchemySessionStore`, which wraps `agents.extensions.memory.SQLAlchemySession`.
- Tables are explicitly named `sdk_agent_sessions` and `sdk_agent_session_messages` (set in `session_store.py`) to avoid clashing with our own `agent_messages` table.
- Table DDL comes from Alembic migration `6724700351b6_add_sdk_session_columns.py`; auto-creation is enabled only for SQLite (tests). Run `just migrate` for Postgres.
- `sdk_agent_sessions`: `session_id` PK plus `created_at/updated_at`.
- `sdk_agent_session_messages`: `id` PK, `session_id` FK → `sdk_agent_sessions`, `message_data` TEXT (serialized SDK items), `created_at`, and an index on `(session_id, created_at)`.
- Session IDs prefer the provider Conversation ID (`conv_*` stored on `agent_conversations.provider_conversation_id`); we fall back to our UUID when no provider ID exists.
- Our durable app history remains in `agent_conversations` / `agent_messages`; the SDK tables mirror the same turns in the format the OpenAI runtime expects.

## Operational notes
- Build the provider via `build_openai_provider(...)` (see `provider.py`); it injects the shared async engine into the session store and wires the conversation search callback for tool resolver search.
- If the SDK tables look empty, confirm the migration ran and that the provider is using Postgres (not the in-memory SQLite test engine).
