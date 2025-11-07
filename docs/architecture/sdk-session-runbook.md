# SDK Session Runbook

## Purpose
- Ensure OpenAI Agents SDK sessions share the same PostgreSQL instance as the rest of the service.
- Guarantee every FastAPI pod configures the session store during startup so chat history persists without manual prompt stitching.
- Provide operators with clear validation and recovery steps.

## Components
- **Tables**: `sdk_agent_sessions`, `sdk_agent_session_messages` (migrations add both; no auto-creation at runtime).
- **Engine source**: Shared async engine configured via `init_engine()`; the lifespan hook calls `configure_sdk_session_store(engine)`.
- **Application hooks**: `AgentService` pulls/updates session metadata via `ConversationService`, then calls `Runner.run(..., session=...)`.

## Provisioning Checklist
1. Run `make migrate` (uses `.env.compose` + local env) to apply `6724700351b6_add_sdk_session_columns`.
2. Verify the tables exist:
   ```sql
   \d sdk_agent_sessions;
   \d sdk_agent_session_messages;
   ```
3. Confirm `agent_conversations` contains the new columns (`sdk_session_id`, `session_cursor`, `last_session_sync_at`).

## Runtime Health Checks
- `/health/ready` already covers the database; no extra endpoint required. However, Grafana dashboards should alert on:
  - Excessive rows in `sdk_agent_session_messages` (indicates retention leak).
  - Absence of new `sdk_session_id` values for recent `agent_conversations`.
- Periodically run:
  ```sql
  SELECT COUNT(*) FROM sdk_agent_sessions;
  SELECT session_id, COUNT(*) FROM sdk_agent_session_messages GROUP BY 1 ORDER BY 2 DESC LIMIT 5;
  ```

## Recovery Procedures
1. **Corrupted session history**: Delete from `sdk_agent_session_messages` for the affected `session_id` and blank the associated columns on `agent_conversations`. Agents will rebuild state from durable conversation logs.
2. **Rolling back code**: Downgrade the migration (`alembic downgrade 45c4400e74d9`) only after clearing the new columns/tables.
3. **Stuck migrations**: Use `make migrate` to rerun with verbose output; all SQL runs inside the managed virtualenv.

## Local Development Notes
- Tests rely on the new tables; ensure `pytest -m postgres` runs against a database that has the migration.
- The in-memory `EphemeralConversationRepository` now mirrors `ConversationSessionState`, so unit tests can run without PostgreSQL.
- Developers can inspect session payloads locally with:
  ```sql
  SELECT session_id, message_data FROM sdk_agent_session_messages ORDER BY created_at DESC LIMIT 10;
  ```
