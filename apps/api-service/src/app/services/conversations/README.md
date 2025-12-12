# Conversations services

Developer-facing overview of the pieces that persist and surface conversation data for chat/agent flows. These sit above the repository layer and are wired through the application container.

## What this area does
- Persists conversation messages, run events, run usage, session state, and memory config via `ConversationService` (façade over the domain `ConversationRepository`).
- Serves read APIs (list/search/history/memory/events) through `ConversationQueryService` and the `api/v1/conversations` router.
- Emits lightweight metadata events (e.g., generated titles) over an in-memory stream for the UI.
- Generates conversation titles asynchronously after the first user message.

## Key modules
- `conversation_service.py`: Core façade that enforces tenant scoping and delegates to the configured `ConversationRepository` (Postgres by default via `infrastructure/persistence/conversations/postgres.py`). Also logs creation/clear events to `activity_service` best-effort.
- `conversations/title_service.py`: Small helper that asks an SDK `Agent` (default `gpt-5-mini`, 2s timeout) to produce a short title, persists it via `ConversationService.set_display_name`, and publishes a metadata event. Wired in `bootstrap/container.py` as `title_service`.
- `conversations/metadata_stream.py`: In-memory async pub/sub used for best-effort metadata fan-out; backs `/api/v1/conversations/{id}/stream` SSE. State is per-process—do not rely on it for durable events.
- `services/agents/query.py`: Read-only layer that composes `ConversationService` with `ConversationHistoryService` for list/search/history/messages/event reads.
- `api/v1/conversations/router.py`: Public endpoints for listing, searching, reading history/messages/events, updating memory config, deleting conversations, and streaming metadata.

## Lifecycle in agent runs (where it is used)
- `services/agents/run_pipeline.py` uses `ConversationService` to append user/assistant messages with `ConversationMetadata`, load/apply memory configs, fetch cross-session summaries, persist run events, and upsert session state.
- `services/agents/usage.py` records per-run token usage back into `ConversationService.persist_run_usage` so audit/billing views can reuse the same data.
- `TitleService.generate_if_absent` is typically triggered after the first user turn to name the thread and push a `conversation.title.generated` metadata event to listeners.

## Persistence shape
- Domain contracts live in `app/domain/conversations.py` (messages, attachments, summaries, memory config, run events/usage, etc.).
- Postgres implementation is composed of focused stores (`message_store`, `search_store`, `run_event_store`, `summary_store`, `usage_store`) under `infrastructure/persistence/conversations/`.
- All operations require a `tenant_id`; helper guards in `ConversationService` enforce this and validate metadata tenant consistency.

## How to work with it
- Use `get_conversation_service()` from the container when persisting chat data or session state; set a new repository via `ConversationService.set_repository` during startup wiring if you replace storage.
- Use `get_conversation_query_service()` when serving read-only views (list/search/history/messages/events) to keep read paths isolated from orchestration logic.
- Subscribe to metadata events in the UI via `GET /api/v1/conversations/{conversation_id}/stream`; events are JSON strings with a `timestamp`.
- When extending metadata (e.g., new async annotations), publish through `metadata_stream.publish(...)` and document the shape in the router schema.
