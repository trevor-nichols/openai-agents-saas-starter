# Conversations services

Developer-facing overview of the pieces that persist and surface conversation data for chat/agent flows. These sit above the repository layer and are wired through the application container.

## What this area does
- Persists conversation messages, run events, run usage, session state, and memory config via `ConversationService` (façade over the domain `ConversationRepository`).
- Serves read APIs (list/search/history/memory/events) through `ConversationQueryService` and the `api/v1/conversations` router.
- Streams and persists conversation titles derived from the first user message.

## Key modules
- `conversation_service.py`: Core façade that enforces tenant scoping and delegates to the configured `ConversationRepository` (Postgres by default via `infrastructure/persistence/conversations/postgres.py`). Also logs creation/clear events to `activity_service` best-effort.
- `conversations/title_service.py`: Small helper that streams an SDK `Agent` (default `gpt-5-nano`, 5s timeout) and persists the final title via `ConversationService.set_display_name`. The streaming endpoint is `/api/v1/conversations/{conversation_id}/stream`.
- `services/agents/query.py`: Read-only layer that composes `ConversationService` with `ConversationHistoryService` for list/search/history/messages/event reads.
- `api/v1/conversations/router.py`: Public endpoints for listing, searching, reading history/messages/events, updating memory config, deleting conversations, and streaming conversation titles.

## Lifecycle in agent runs (where it is used)
- `services/agents/run_pipeline.py` uses `ConversationService` to append user/assistant messages with `ConversationMetadata`, load/apply memory configs, fetch cross-session summaries, persist run events, and upsert session state.
- `services/agents/usage.py` records per-run token usage back into `ConversationService.persist_run_usage` so audit/billing views can reuse the same data.
- `GET /api/v1/conversations/{conversation_id}/stream` streams the LLM-generated title text and persists it once complete.

## Persistence shape
- Domain contracts live in `app/domain/conversations.py` (messages, attachments, summaries, memory config, run events/usage, etc.).
- Postgres implementation is composed of focused stores (`message_store`, `search_store`, `run_event_store`, `summary_store`, `usage_store`) under `infrastructure/persistence/conversations/`.
- All operations require a `tenant_id`; helper guards in `ConversationService` enforce this and validate metadata tenant consistency.

## How to work with it
- Use `get_conversation_service()` from the container when persisting chat data or session state; set a new repository via `ConversationService.set_repository` during startup wiring if you replace storage.
- Use `get_conversation_query_service()` when serving read-only views (list/search/history/messages/events) to keep read paths isolated from orchestration logic.
- Generate a title client-side by opening `GET /api/v1/conversations/{conversation_id}/stream` and rendering each SSE `data:` chunk as it arrives. The stream emits `data: [DONE]` once complete.
