# SDK Session Runbook

## Purpose
- Ensure OpenAI Agents SDK sessions share the same PostgreSQL instance as the rest of the service.
- Guarantee every FastAPI pod configures the session store during startup so chat history persists without manual prompt stitching.
- Provide operators with clear validation and recovery steps.
- Keep provider-hosted conversation IDs (`conv_*`) aligned with our UUID threads so SDK state and durable logs stay correlated.

## Components
- **Tables**: `sdk_agent_sessions`, `sdk_agent_session_messages` (migrations add both; no auto-creation at runtime).
- **Provider state**: `agent_conversations.provider` and `agent_conversation.provider_conversation_id` store the OpenAI `conv_*` ID we hand to the SDK; session store keys use that ID when present.
- **Engine source**: Shared async engine configured via `init_engine()`; FastAPI bootstrap passes it into `build_openai_provider(..., engine=engine)` which constructs the SQLAlchemy session store.
- **Application hooks**: `AgentService` pulls/updates session metadata via `ConversationService`, then requests session handles from `provider.session_store.build(session_id)` and feeds them to the OpenAI runtime. Session IDs prefer the provider `conv_*` when available; otherwise they fall back to our UUID.

## Provisioning Checklist
1. Run `just migrate` (uses `.env.compose` + local env) to apply session + provider conversation migrations (`6724700351b6_add_sdk_session_columns`, `20251122_130000_add_provider_conversation_ids`, and merge head).
2. Verify the tables exist:
   ```sql
   \d sdk_agent_sessions;
   \d sdk_agent_session_messages;
   ```
3. Confirm `agent_conversations` contains the new columns (`provider`, `provider_conversation_id`, `sdk_session_id`, `session_cursor`, `last_session_sync_at`).

## Runtime Health Checks
- `/health/ready` already covers the database; no extra endpoint required. However, Grafana dashboards should alert on:
  - Excessive rows in `sdk_agent_session_messages` (indicates retention leak).
  - Absence of new `sdk_session_id` values for recent `agent_conversations`.
  - Missing `provider_conversation_id` for active conversations (indicates failed OpenAI Conversation creation).
- Periodically run:
  ```sql
  SELECT COUNT(*) FROM sdk_agent_sessions;
  SELECT session_id, COUNT(*) FROM sdk_agent_session_messages GROUP BY 1 ORDER BY 2 DESC LIMIT 5;
  ```

## Recovery Procedures
1. **Corrupted session history**: Delete from `sdk_agent_session_messages` for the affected `session_id` and blank the associated columns on `agent_conversations`. Agents will rebuild state from durable conversation logs.
2. **Missing/invalid provider conv IDs**: Clear `provider_conversation_id` for the affected conversation; the next request will recreate it. Session handles continue using the existing `sdk_session_id` to preserve history unless you set `FORCE_PROVIDER_SESSION_REBIND=true`, which forces the session store to rebind to the new `conv_*` (expect a cold session unless you migrate rows manually).
3. **Rolling back code**: Downgrade the migration (`alembic downgrade 45c4400e74d9`) only after clearing the new columns/tables, and also drop `provider_conversation_id`/`provider` (`alembic downgrade 20251122_130000`).
3. **Stuck migrations**: Use `just migrate` to rerun with verbose output; all SQL runs inside the managed virtualenv.

## Local Development Notes
- Provider bootstrap in tests uses the in-memory SQLite engine via `build_openai_provider` (see `api-service/tests/conftest.py`).
- The in-memory `EphemeralConversationRepository` mirrors `ConversationSessionState`, so unit tests can run without PostgreSQL.
- Developers can inspect session payloads locally with:
  ```sql
  SELECT session_id, message_data FROM sdk_agent_session_messages ORDER BY created_at DESC LIMIT 10;
  ```
