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

## Memory strategies (trim/summarize/compact) and prompt injection
- **Purpose**: Keep the SDK session context lean while leaving our durable audit history untouched. Strategies operate only on the SDK session items, not on `agent_messages`.
- **Configuration precedence**: request (`AgentChatRequest.memory_strategy` / `memory_injection`) → conversation defaults (columns on `agent_conversations`) → agent spec defaults (`memory_strategy_defaults` on the OpenAI descriptor). Resolved in `build_memory_strategy_config`/`resolve_memory_injection`.
- **Runtime wiring**: During `prepare_run_context`, we pass the resolved config to `SessionManager.acquire_session`, which wraps the SDK session in `StrategySession` (see `memory/strategy.py`). `StrategySession` pulls current items, applies the strategy, clears, and rewrites the SDK session so generation sees the trimmed/compacted view.
- **Strategies**:
  - `NONE`: pass-through.
  - `TRIM`: drop oldest user-anchored turns beyond `max_user_turns`, keep the last `keep_last_user_turns`.
  - `SUMMARIZE`: same turn trigger; collapses older turns into a summary prefix + assistant summary. Optional `on_summary` hook can persist the text.
  - `COMPACT`: trigger on turn count; keeps last K turns and replaces older tool inputs/outputs with placeholders, optionally skipping excluded tools and clearing tool inputs.
- **Prompt-level injection**: If `memory_injection` resolves true and a recent summary exists (`conversation_summaries` via `ConversationSummaryStore`), `prepare_run_context` attaches the summary to the runtime context for prompt reuse without replaying the full history.
- **Event log resiliency**: Because `StrategySession` rewrites history, `project_new_session_items` now diffs by fingerprints (stable IDs + content hash) instead of list-length slicing, so new SDK items still flow into the structured event log even when earlier turns are trimmed.
- **Surfaces**: Configuration is exposed through the Conversations API; specs only provide defaults. Workflows inherit the behavior automatically because they invoke the same provider/session plumbing.

## Operational notes
- Build the provider via `build_openai_provider(...)` (see `provider.py`); it injects the shared async engine into the session store and wires the conversation search callback for tool resolver search.
- If the SDK tables look empty, confirm the migration ran and that the provider is using Postgres (not the in-memory SQLite test engine).
