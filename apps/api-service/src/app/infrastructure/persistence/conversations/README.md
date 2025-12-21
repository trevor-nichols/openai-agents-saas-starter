# Conversation persistence

Persistence layer for conversations, messages, summaries, run events, search, and usage. Used by AgentService and workflow runners; does not add or change AgentSpec fields.

## What lives here
- `models.py` — SQLAlchemy models for conversations, messages, runs, events, summaries, usage.
- `postgres.py` — repository implementations over AsyncSession.
- `conversation_store.py` — conversation row persistence (metadata, titles, memory config).
- `conversation_reader.py` — read-model assembly (conversations + messages).
- `message_store.py` — append/read messages with metadata.
- `run_event_store.py` — store per-run/session events (tool calls, guardrails, compaction).
- `summary_store.py` — store and fetch conversation summaries used for memory injection.
- `search_store.py` — search across messages; supports preview payloads.
- `usage_store.py` — usage records for billing/metrics.
- `cursors.py` — pagination helpers for message/event listing.
- `ids.py` — ID helpers for runs and events.
- `mappers.py` — DTO/entity mapping helpers.
- `instrumentation.py` — tracing/logging wrappers.
- `ledger_visibility.py` — shared ledger visibility filters for message queries.

## Relation to agents
- AgentService writes/reads conversation messages and session events here; AgentSpecs are unaffected.
- Memory strategies (summaries/compaction) rely on `summary_store` and session items projected via `run_event_store`.
- Conversation search tool (`search_conversations`) reads from `search_store` to serve agents.

## When to touch this
- Schema/model changes for conversation data.
- Performance/search improvements.
- Adjusting stored metadata for session items, summaries, or usage.
